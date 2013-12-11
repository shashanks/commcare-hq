import logging
from dimagi.utils.logging import log_exception
from corehq.apps.commtrack.models import CommtrackConfig, StockTransaction, SupplyPointCase
from corehq.apps.commtrack import const
import collections
from dimagi.utils.couch.loosechange import map_reduce
from corehq.apps.commtrack.xmlutil import XML
from casexml.apps.case.models import CommCareCaseAction
from casexml.apps.case.xml.parser import AbstractAction

from casexml.apps.case.mock import CaseBlock
from casexml.apps.case.models import CommCareCase
from casexml.apps.case.xml import V2
from xml import etree as legacy_etree
from datetime import datetime, date
from lxml import etree
from corehq.apps.receiverwrapper.util import get_submit_url
from receiver.util import spoof_submission


logger = logging.getLogger('commtrack.incoming')

COMMTRACK_LEGACY_REPORT_XMLNS = 'http://commtrack.org/legacy/stock_report'

# FIXME this decorator is causing me bizarre import issues
#@log_exception()
def process_stock(sender, xform, config=None, **kwargs):
    """process the commtrack xml constructs in an incoming submission"""
    domain = xform.domain

    config = CommtrackConfig.for_domain(domain)
    transactions = list(unpack_commtrack(xform, config))
    # omitted: normalize_transactions (used for bulk requisitions?)
    if not transactions:
        return

    grouped_tx = map_reduce(lambda tx: [((tx.case_id, tx.product_id),)],
                            lambda v: sorted(v, key=lambda tx: (tx.timestamp, tx.processing_order)),
                            data=transactions,
                            include_docs=True)

    supply_point_cases = SupplyPointCase.view('_all_docs',
                                              keys=list(set(k[0] for k in grouped_tx)),
                                              include_docs=True)
    supply_point_product_subcases = dict((sp._id, product_subcases(sp)) for sp in supply_point_cases)

    user_id = xform.form['meta']['userID']
    submit_time = xform['received_on']

    # touch the supply point cases
    for spc in supply_point_cases:
        case_action = CommCareCaseAction.from_parsed_action(submit_time, user_id, xform, AbstractAction('commtrack'))
        spc.actions.append(case_action)
        spc.save()

    post_processed_transactions = []
    E = XML(ns=COMMTRACK_LEGACY_REPORT_XMLNS)
    root = E.commtrack_data()
    for (supply_point_id, product_id), txs in grouped_tx.iteritems():
        subcase = supply_point_product_subcases[supply_point_id][product_id]

        case_block, reconciliations = process_product_transactions(user_id, submit_time, subcase, txs)
        root.append(case_block)
        post_processed_transactions.extend(reconciliations)

        #req_txs = requisition_transactions.get(product_id, [])
        #if req_txs and config.requisitions_enabled:
        #    req = RequisitionState.from_transactions(user_id, product_case, req_txs)
        #    case_block = etree.fromstring(req.to_xml())
        #    root.append(case_block)

    post_processed_transactions.extend(map(lambda tx: LegacyStockTransaction.convert(tx, supply_point_product_subcases), transactions))
    set_transactions(root, post_processed_transactions, E)

    submission = etree.tostring(root, encoding='utf-8', pretty_print=True)
    logger.debug(submission)
    spoof_submission(get_submit_url(domain), submission,
                     headers={'HTTP_X_SUBMIT_TIME': submit_time},
                     hqsubmission=False)




# TODO retire this with move to new data model
def product_subcases(supply_point):
    """given a supply point, return all the sub-cases for each product stocked at that supply point
    actually returns a mapping: product doc id => sub-case
    ACTUALLY returns a dict that will create non-existent product sub-cases on demand
    """
    from helpers import make_supply_point_product

    product_subcase_uuids = [ix.referenced_id for ix in supply_point.reverse_indices if ix.identifier == const.PARENT_CASE_REF]
    product_subcases = CommCareCase.view('_all_docs', keys=product_subcase_uuids, include_docs=True)
    product_subcase_mapping = dict((subcase.dynamic_properties().get('product'), subcase) for subcase in product_subcases)

    def create_product_subcase(product_uuid):
        return make_supply_point_product(supply_point, product_uuid)

    class DefaultDict(dict):
        """similar to collections.defaultdict(), but factory function has access
        to 'key'
        """
        def __init__(self, factory, *args, **kwargs):
            super(DefaultDict, self).__init__(*args, **kwargs)
            self.factory = factory

        def __getitem__(self, key):
            if key in self:
                val = self.get(key)
            else:
                val = self.factory(key)
                self[key] = val
            return val

    return DefaultDict(create_product_subcase, product_subcase_mapping)

def unpack_commtrack(xform, config):
    global_context = {
        'timestamp': xform.received_on,
    }

    def commtrack_nodes(data):
        for tag, nodes in data.iteritems():
            for node in (nodes if isinstance(nodes, collections.Sequence) else [nodes]):
                if not hasattr(node, '__iter__'):
                    continue
                if node.get('@xmlns', data['@xmlns']) == const.COMMTRACK_REPORT_XMLNS:
                    yield (tag, node)
    for elem in commtrack_nodes(xform.form):
        # FIXME deal with requisitions later
        tag, node = elem
        products = node['product']
        if not isinstance(products, collections.Sequence):
            products = [products]
        for prod_entry in products:
            yield StockTransaction.from_xml(config, global_context, tag, node, prod_entry)

def set_transactions(root, new_tx, E):
    for tx in new_tx:
        root.append(tx.to_legacy_xml(E))

def process_product_transactions(user_id, timestamp, case, txs):
    """process all the transactions from a stock report for an individual
    product. we have to apply them in bulk because each one may update
    the case state that the next one works off of. therefore we have to
    keep track of the updated case state ourselves
    """
    current_state = StockState(case, timestamp)
    reconciliations = []

    i = [0] # annoying python 2.x scope issue
    def set_order(tx):
        tx.processing_order = i[0]
        i[0] += 1

    for tx in txs:
        recon = current_state.update(tx.action, tx.quantity)
        if recon:
            set_order(recon)
            reconciliations.append(recon)
        set_order(tx)
    return current_state.to_case_block(user_id=user_id), reconciliations

from couchdbkit.ext.django.schema import *
class LegacyStockTransaction(StockTransaction):
    product_subcase = StringProperty()

    def to_legacy_xml(self, E):
        attr = {}
        if self.subaction == const.INFERRED_TRANSACTION:
            attr['inferred'] = 'true'
        if self.processing_order is not None:
            attr['order'] = str(self.processing_order + 1)

        return E.transaction(
            E.product(self.product_id),
            E.product_entry(self.product_subcase),
            E.action((self.subaction if self.subaction != const.INFERRED_TRANSACTION else None) or self.action),
            E.value(str(self.quantity)),
            **attr
        )

    @classmethod
    def convert(cls, tx, product_subcases):
        ltx = LegacyStockTransaction(**dict(tx.iteritems()))
        ltx.product_subcase = product_subcases[tx.case_id][tx.product_id]._id
        return ltx

class StockState(object):
    def __init__(self, case, reported_on):
        self.case = case
        self.last_reported = reported_on
        props = case.dynamic_properties()
        self.current_stock = int(props.get('current_stock') or 0)  # int
        self.stocked_out_since = props.get('stocked_out_since')  # date

    def update(self, action_type, value):
        """given the current stock state for a product at a location, update
        with the incoming datapoint
        
        fancy business logic to reconcile stock reports lives HERE
        """
        reconciliation_transaction = None
        def mk_reconciliation(diff):
            return LegacyStockTransaction(
                product_id=self.case.product,
                product_subcase=self.case._id,
                action=const.StockActions.RECEIPTS if diff > 0 else const.StockActions.CONSUMPTION,
                quantity=abs(diff),
                inferred=True,
            )

        if action_type == const.StockActions.STOCKOUT:
            if self.current_stock > 0:
                reconciliation_transaction = mk_reconciliation(-self.current_stock)

            self.current_stock = 0
            if not self.stocked_out_since:
                self.stocked_out_since = date.today()

        else:
            if action_type == const.StockActions.STOCKONHAND:
                if self.current_stock != value:
                    reconciliation_transaction = mk_reconciliation(value - self.current_stock)
                self.current_stock = value
            elif action_type == const.StockActions.RECEIPTS:
                self.current_stock += value
            elif action_type == const.StockActions.CONSUMPTION:
                self.current_stock -= value

            # data normalization
            if self.current_stock > 0:
                self.stocked_out_since = None
            else:
                self.current_stock = 0 # handle if negative
                if not self.stocked_out_since: # handle if stocked out date already set
                    self.stocked_out_since = date.today()

        return reconciliation_transaction

    def to_case_block(self, user_id=None):
        def convert_prop(val):
            return str(val) if val is not None else ''

        props = ['current_stock', 'stocked_out_since', 'last_reported']

        case_update = CaseBlock(
            version=V2,
            case_id=self.case._id,
            user_id=user_id or 'FIXME',
            update=dict((k, convert_prop(getattr(self, k))) for k in props)
        ).as_xml()
        # convert xml.etree to lxml
        case_update = etree.fromstring(legacy_etree.ElementTree.tostring(case_update))

        return case_update
