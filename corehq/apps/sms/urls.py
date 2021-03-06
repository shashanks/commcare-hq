from django.conf.urls.defaults import patterns, url
from corehq.apps.sms.views import (
    DomainSmsGatewayListView,
)

urlpatterns = patterns('corehq.apps.sms.views',
    url(r'^$', 'default', name='sms_default'),
    url(r'^post/?$', 'post', name='sms_post'),
    url(r'^send_to_recipients/$', 'send_to_recipients'),
    url(r'^compose/$', 'compose_message', name='sms_compose_message'),
    url(r'^message_test/(?P<phone_number>\d+)/$', 'message_test', name='message_test'),
    url(r'^api/send_sms/$', 'api_send_sms', name='api_send_sms'),
    url(r'^history/$', 'messaging', name='messaging'),
    url(r'^forwarding_rules/$', 'list_forwarding_rules', name='list_forwarding_rules'),
    url(r'^add_forwarding_rule/$', 'add_forwarding_rule', name='add_forwarding_rule'),
    url(r'^edit_forwarding_rule/(?P<forwarding_rule_id>[\w-]+)/$', 'add_forwarding_rule', name='edit_forwarding_rule'),
    url(r'^delete_forwarding_rule/(?P<forwarding_rule_id>[\w-]+)/$', 'delete_forwarding_rule', name='delete_forwarding_rule'),
    url(r'^add_backend/(?P<backend_class_name>[\w-]+)/$', 'add_domain_backend', name='add_domain_backend'),
    url(r'^edit_backend/(?P<backend_class_name>[\w-]+)/(?P<backend_id>[\w-]+)/$', 'add_domain_backend', name='edit_domain_backend'),
    url(r'^list_backends/$', 'list_domain_backends', name='list_domain_backends'),
    url(r'^gateways/$', DomainSmsGatewayListView.as_view(), name=DomainSmsGatewayListView.urlname),
    url(r'^delete_backend/(?P<backend_id>[\w-]+)/$', 'delete_domain_backend', name='delete_domain_backend'),
    url(r'^set_default_domain_backend/(?P<backend_id>[\w-]+)/$', 'set_default_domain_backend', name='set_default_domain_backend'),
    url(r'^unset_default_domain_backend/(?P<backend_id>[\w-]+)/$', 'unset_default_domain_backend', name='unset_default_domain_backend'),
    url(r'^chat_contacts/$', 'chat_contacts', name='chat_contacts'),
    url(r'^chat/(?P<contact_id>[\w-]+)/$', 'chat', name='sms_chat'),
    url(r'^api/history/$', 'api_history', name='api_history'),
    url(r'^settings/$', 'sms_settings', name='sms_settings'),
)

sms_admin_interface_urls = patterns('corehq.apps.sms.views',
    url(r'^$', 'default_sms_admin_interface', name="default_sms_admin_interface"),
    url(r'^backends/$', 'list_backends', name="list_backends"),
    url(r'^add_backend/(?P<backend_class_name>[\w-]+)/$', 'add_backend', name="add_backend"),
    url(r'^edit_backend/(?P<backend_class_name>[\w-]+)/(?P<backend_id>[\w-]+)/$', 'add_backend', name='edit_backend'),
    url(r'^delete_backend/(?P<backend_id>[\w-]+)/$', 'delete_backend', name='delete_backend'),
    url(r'^global_backend_map/$', 'global_backend_map', name='global_backend_map'),
)
