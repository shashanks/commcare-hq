from django.conf.urls.defaults import patterns, url, include
from corehq.apps.hqmedia.urls import application_urls as hqmedia_urls

app_urls = patterns('corehq.apps.app_manager.views',
    url(r'^languages/$', 'view_app', name='app_languages'),
    url(r'^languages/translations/download/$', 'download_translations', name='download_translations'),
    url(r'^languages/translations/upload/$', 'upload_translations', name='upload_translations'),
    url(r'^multimedia/$', 'view_app', name='app_multimedia'),
    url(r'^copy/$', 'view_app', name='app_copy'),
    url(r'^delete/$', 'view_app', name='app_delete'),
    url(r'^$', 'view_app', name='view_app'),
    url(r'^releases/$', 'release_manager', name='release_manager'),
    url(r'^current_version/$', 'current_app_version', name='current_app_version'),
    url(r'^releases/json/$', 'paginate_releases', name='paginate_releases'),
    url(r'^releases/release/(?P<saved_app_id>[\w-]+)/$', 'release_build',
        name='release_build'),
    url(r'^releases/unrelease/(?P<saved_app_id>[\w-]+)/$', 'release_build',
        name='unrelease_build', kwargs={'is_released': False}),
    url(r'^modules-(?P<module_id>[\w-]+)/$', 'view_module', name='view_module'),
    url(r'^modules-(?P<module_id>[\w-]+)/forms-(?P<form_id>[\w-]+)/$',
        'view_form', name='view_form'),
    url(r'^user_registration/$', 'view_user_registration',
        name='view_user_registration'),
    url(r'^user_registration/source/$', 'user_registration_source',
        name='user_registration_source'),
    url(r'^modules-(?P<module_id>[\w-]+)/forms-(?P<form_id>[\w-]+)/source/$',
        'form_source', name='form_source'),
    url(r'^summary/$', 'app_summary', name='app_summary'),
    url(r'^exchange_summary/$', 'app_summary_from_exchange',
        name='exchange_app_summary'),
)

urlpatterns = patterns('corehq.apps.app_manager.views',
    url(r'^$', 'default'),
    url(r'^xform/(?P<form_unique_id>[\w-]+)/$', 'xform_display'),
    url(r'^browse/(?P<app_id>[\w-]+)/modules-(?P<module_id>[\w-]+)/forms-(?P<form_id>[\w-]+)/source/$',
        'get_xform_source', name='get_xform_source'),
    url(r'^browse/(?P<app_id>[\w-]+)/user_registration/source/$',
        'get_user_registration_source', name='get_user_registration_source'),
    url(r'^casexml/(?P<form_unique_id>[\w-]+)/$', 'form_casexml'),
    url(r'^source/(?P<app_id>[\w-]+)/$', 'app_source'),
    url(r'^import_app/$', 'import_app', name='import_app'),
    url(r'^copy_app/$', 'copy_app', name='copy_app'),
    url(r'^view/(?P<app_id>[\w-]+)/', include(app_urls)),
    url(r'^new_module/(?P<app_id>[\w-]+)/$', 'new_module'),
    url(r'^new_app/$', 'new_app', name='new_app'),
    url(r'^new_form/(?P<app_id>[\w-]+)/(?P<module_id>[\w-]+)/$', 'new_form'),

    url(r'^delete_app/(?P<app_id>[\w-]+)/$', 'delete_app'),
    url(r'^delete_module/(?P<app_id>[\w-]+)/(?P<module_id>[\w-]+)/$',
        'delete_module', name="delete_module"),
    url(r'^delete_form/(?P<app_id>[\w-]+)/(?P<module_id>[\w-]+)/(?P<form_id>[\w-]+)/$',
        'delete_form', name="delete_form"),

    url(r'^copy_form/(?P<app_id>[\w-]+)/(?P<module_id>[\w-]+)/(?P<form_id>[\w-]+)/$',
        'copy_form', name='copy_form'),

    url(r'^undo_delete_app/(?P<record_id>[\w-]+)/$', 'undo_delete_app',
        name='undo_delete_app'),
    url(r'^undo_delete_module/(?P<record_id>[\w-]+)/$', 'undo_delete_module',
        name='undo_delete_module'),
    url(r'^undo_delete_form/(?P<record_id>[\w-]+)/$', 'undo_delete_form',
        name='undo_delete_form'),

    url(r'^edit_form_attr/(?P<app_id>[\w-]+)/(?P<unique_form_id>[\w-]+)/(?P<attr>[\w-]+)/$',
        'edit_form_attr', name='edit_form_attr'),
    url(r'^patch_xform/(?P<app_id>[\w-]+)/(?P<unique_form_id>[\w-]+)/$',
        'patch_xform', name='patch_xform'),
    url(r'^validate_form_for_build/(?P<app_id>[\w-]+)/(?P<unique_form_id>[\w-]+)/$',
        'validate_form_for_build', name='validate_form_for_build'),
    url(r'^rename_language/(?P<form_unique_id>[\w-]+)/$', 'rename_language'),
    url(r'^validate_langcode/(?P<app_id>[\w-]+)/$', 'validate_language'),
    url(r'^edit_form_actions/(?P<app_id>[\w-]+)/(?P<module_id>[\w-]+)/(?P<form_id>[\w-]+)/$',
        'edit_form_actions'),
    url(r'^edit_careplan_form_actions/(?P<app_id>[\w-]+)/(?P<module_id>[\w-]+)/(?P<form_id>[\w-]+)/$',
        'edit_careplan_form_actions'),
    # multimedia stuff
    url(r'^multimedia/(?P<app_id>[\w-]+)/download/$',
        'multimedia_list_download', name='multimedia_list_download'),
    url(r'^(?P<app_id>[\w-]+)/multimedia/', include(hqmedia_urls)),

    url(r'^edit_module_detail_screens/(?P<app_id>[\w-]+)/(?P<module_id>[\w-]+)/$',
        'edit_module_detail_screens', name='edit_module_detail_screens'),
    url(r'^edit_module_attr/(?P<app_id>[\w-]+)/(?P<module_id>[\w-]+)/(?P<attr>[\w-]+)/$',
        'edit_module_attr'),

    url(r'^commcare_profile/(?P<app_id>[\w-]+)/$', 'commcare_profile'),
    url(r'^edit_commcare_profile/(?P<app_id>[\w-]+)/$', 'edit_commcare_profile',
        name='edit_commcare_profile'),
    url(r'^edit_commcare_settings/(?P<app_id>[\w-]+)/$',
        'edit_commcare_settings', name='edit_commcare_settings'),
    url(r'^edit_app_langs/(?P<app_id>[\w-]+)/$', 'edit_app_langs',
        name='edit_app_langs'),
    url(r'^edit_app_attr/(?P<app_id>[\w-]+)/(?P<attr>[\w-]+)/$',
        'edit_app_attr', name='edit_app_attr'),
    url(r'^edit_app_translations/(?P<app_id>[\w-]+)/$', 'edit_app_translations',
        name='edit_app_translations'),

    url(r'^rearrange/(?P<app_id>[\w-]+)/(?P<key>[\w-]+)/$', 'rearrange'),

    url(r'^odk/(?P<app_id>[\w-]+)/qr_code/$', 'odk_qr_code'),
    url(r'^odk/(?P<app_id>[\w-]+)/media_qr_code/$', 'odk_media_qr_code'),
    url(r'^odk/(?P<app_id>[\w-]+)/install/$', 'odk_install', name="odk_install"),
    url(r'^odk/(?P<app_id>[\w-]+)/media_install/$', 'odk_install', {'with_media': True}, name="odk_media_install"),

    url(r'^save/(?P<app_id>[\w-]+)/$', 'save_copy'),
    url(r'^revert/(?P<app_id>[\w-]+)/$', 'revert_to_copy'),
    url(r'^delete_copy/(?P<app_id>[\w-]+)/$', 'delete_copy'),

    url(r'^emulator/(?P<app_id>[\w-]+)/$', 'emulator_handler', name="emulator"),
    url(r'^emulator/(?P<app_id>[\w-]+)/CommCare\.jar$', 'emulator_commcare_jar'),
    url(r'^download/(?P<app_id>[\w-]+)/$', 'download_index', {}, 'download_index'),
    url(r'^download/(?P<app_id>[\w-]+)/(?P<path>.*)$', 'download_file',
        name='app_download_file'),
    url(r'^download/(?P<app_id>[\w-]+)/',
        include('corehq.apps.app_manager.download_urls')),
    url(r'^formdefs/(?P<app_id>[\w-]+)/', 'formdefs', name='formdefs'),
)
