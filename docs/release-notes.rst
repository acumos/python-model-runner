.. ===============LICENSE_START============================================================
.. Acumos CC-BY-4.0
.. ========================================================================================
.. Copyright (C) 2017-2020 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
.. Modifications Copyright (C) 2020 Nordix Foundation.
.. ========================================================================================
.. This Acumos documentation file is distributed by AT&T and Tech Mahindra
.. under the Creative Commons Attribution 4.0 International License (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
.. http://creativecommons.org/licenses/by/4.0
..
.. This file is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
.. ===============LICENSE_END==============================================================

========================================
Acumos Python Model Runner Release Notes
========================================

v0.2.24, 15 May 2020
====================
- Fix OpenAPI spec generation for empty inputs `ACUMOS-4010 <https://jira.acumos.org/browse/ACUMOS-4010>`_
- Allow the model runner to use raw data types `ACUMOS-3956 <https://jira.acumos.org/browse/ACUMOS-3956>`_
- Receive the licence profile from the running micro-service `ACUMOS-3161 <https://jira.acumos.org/browse/ACUMOS-3161>`_

v0.2.3, 23 January 2020
=======================
- larkparser lark-parser<0.8.0 pinning to prevent error
- Fixing issue with using 0.6.0 model metadata schema - works with model metadata versions <0.6.0 and 0.6.0
- python removing 3.4 support

v0.2.2
======
- Fixed 404 bug for model artifact resources caused by relative model directory
- Fixed incorrect media type for protobuf resource

v0.2.1
======
- Upgraded Swagger UI from v2 to v3

v0.2.0
======
- Overhaul of model runner API
- Added support for ``application/json`` via ``Content-Type`` and ``Accept`` headers
- Added automatic generation of `OpenAPI Specification <https://swagger.io/docs/specification/2-0/basic-structure/>`__ and `Swagger UI <https://swagger.io/tools/swagger-ui/>`__
- Added support for CORS

v0.1.0
======
- Model runner implementation split off from `Acumos Python client <https://pypi.org/project/acumos/>`__ project
