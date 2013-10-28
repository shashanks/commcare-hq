==========
Fake Data
==========

This module lets you generate fake users, cases, and form submissions for
testing the scalability of HQ.
View and edit ``fake_it.py`` to run, and to change the numbers created.


Notes
=====

This data is very time consuming to create at scale.

Inital goal was
1k web users
10k cc users with
    ~100 cases, each with
        ~4 forms
(1M cases total)

Numbers were randomized, so a given user would have anywhere from 0 to 200 cases, for instance.
This goal ended up being unrealistic - rough calculations based on initial data suggested that
to run this process would take something like 3 days of continuous operation.

A server was set up to run long-term processes.  This has not been utilized yet.

Currently I'm creating just users (with no cases or form data)
and it's creating around ~100 users per minute.

To create users, there are a number of db calls, including a bunch by auditcare.
Here are the calls required to make a user:

        [info] [<0.8714.5>] 127.0.0.1 - - GET /performance_db/_design/users/_view/by_username?key=%22joeypierce8949%22&include_docs=true 200
        [info] [<0.8714.5>] 127.0.0.1 - - GET /performance_db/_design/users/_view/by_username?key=%22joeypierce8949%22&include_docs=true 200
        [info] [<0.1221.0>] Starting index update for db: performance_db__auditcare idx: _design/auditcare
        [info] [<0.1221.0>] Index update finished for db: performance_db__auditcare idx: _design/auditcare
        [info] [<0.8714.5>] 127.0.0.1 - - GET /performance_db__auditcare/_design/auditcare/_view/model_actions_by_id?reduce=false&key=%5B%22User%22%2C+%2210856%22%5D 200
        [info] [<0.8714.5>] 127.0.0.1 - - PUT /performance_db__auditcare/89b55f80b97353e42fe6192dcd9c6958 201
        [info] [<0.8714.5>] 127.0.0.1 - - GET /performance_db/_design/users/_view/by_username?key=%22joeypierce8949%22 200
        [info] [<0.1221.0>] Starting index update for db: performance_db__auditcare idx: _design/auditcare
        [info] [<0.1221.0>] Index update finished for db: performance_db__auditcare idx: _design/auditcare
        [info] [<0.8714.5>] 127.0.0.1 - - GET /performance_db__auditcare/_design/auditcare/_view/model_actions_by_id?reduce=false&key=%5B%22User%22%2C+%2210856%22%5D 200
        [info] [<0.8714.5>] 127.0.0.1 - - GET /performance_db__auditcare/89b55f80b97353e42fe6192dcd9c6958 200
        [info] [<0.8714.5>] 127.0.0.1 - - PUT /performance_db__auditcare/89b55f80b97353e42fe6192dcd9c6857 201
        [info] [<0.8714.5>] 127.0.0.1 - - PUT /performance_db/89b55f80b97353e42fe6192dcd7bdaac 201
        [info] [<0.1239.0>] Starting index update for db: performance_db idx: _design/domain
        [info] [<0.8714.5>] 127.0.0.1 - - GET /performance_db/_design/domain/_view/domains?key=%22esoergel%22&reduce=false&include_docs=true&stale=update_after 200
        [info] [<0.1239.0>] Index update finished for db: performance_db idx: _design/domain
        [info] [<0.1183.0>] Starting index update for db: performance_db idx: _design/users
        [info] [<0.1183.0>] Index update finished for db: performance_db idx: _design/users


Next Steps
===========
Trigger long-running task on webscale server to get large amt of cases too.

http://localhost:8000/a/esoergel/api/v0.4/user/
[28/Oct/2013 08:34:22] "GET /a/esoergel/api/v0.4/user/ HTTP/1.1" 200 5613 (time: 14.35s; sql: 0ms (0q))

http://localhost:5984/performance_db/_design/users/_view/by_domain?
        reduce=false&
        startkey=[%22active%22,%22esoergel%22,%22CommCareUser%22]&
        endkey=[%22active%22,%22esoergel%22,%22CommCareUser%22,{}]&
        limit=100&
        skip=100

Report filter loads set of users, paginate this, and be sure to use the reduced version
