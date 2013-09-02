function (doc) {
    if (doc.doc_type === 'XFormInstance' && (doc.domain === 'gsid')) {
        var form = doc.form;

        if (form["@name"] !== 'Malaria Test' && form["@name"] !== 'HIV Test') {
            return;
        }

        emit(
            [doc.domain,
            form["@name"],
            form.test_version,
            form.country,
            form.province,
            form.district,
            form.clinic,
            form.sex,
            doc.received_on,
            form.diagnosis,
            parseInt(form.lot_number, 10)],
            parseInt(form.age, 10)
        );
    }
}
