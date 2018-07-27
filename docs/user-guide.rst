.. ===============LICENSE_START=======================================================
.. Acumos CC-BY-4.0
.. ===================================================================================
.. Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
.. ===================================================================================
.. This Acumos documentation file is distributed by AT&T and Tech Mahindra
.. under the Creative Commons Attribution 4.0 International License (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..      http://creativecommons.org/licenses/by/4.0
..
.. This file is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
.. ===============LICENSE_END=========================================================

.. _userguide-python-model-runner:

=====================================
Acumos Python Model Runner User Guide
=====================================

This tutorial provides a brief overview of ``python-model-runner`` for running
Acumos models.  The model runner is for execution of models created by the ``acumos``
python package, whose source code can be found at the 
`Acumos Python client repository <https://gerrit.acumos.org/r/gitweb?p=acumos-python-client.git;a=summary>`__.

1.  `Background`_
2.  `Running Models`_

Background
==========

Within ``acumos`` running a model consists of loading the serialized archive add_numbers
standing it up with some form of a server.  This package utilizes the 
`Gunicorn <http://gunicorn.org/>`_ webserver and hooks into the 
`Flask <http://flask.pocoo.org/>`_ routing and request infrastructure to
host user models.

Upon initialization, the `acumos client library <https://pypi.org/project/acumos/>`__
is used to parse a model and iterate available endpoints.  Each endpoint is then
exported as an explicit route for users to call over standard HTTP(s) requests.


Executing the Model Runner
==========================

These instructions enumerate steps for running a serialized ``acumos`` model.

1. **Model Data**: First, serialize your model to disk via the ``dump`` functionality in the 
   ``acumos`` python client.  This will produce a directory containing assets
   that contain the model data itself, metadata describing the input and output 
   formats, and actual ``protobuf`` type definitions.

2. **Running Interface**: Second, determine the host IP and port that will be used to access your running model. 

    a. In the example below, classiciation runs on port ``3330``.  This port can be 
       specified with the ``--port`` argument. 

    b. By default, the model runner will attempt to attach to a local IP addess 
       only.  This default is in place for safety and avoidance of accidental 
       exposure of a runner.  *Only one host IP can be utilized at a time.*  To 
       modify the target host IP, utilize the ``--host`` argument.

3. **Cascaded Models**: Third, determine if your model will consume input and respond directly or if
   it will forward the result of a request to another mdoel runner, *downstream*.
   Forwarding is a slightly more advanced usage, but it allows models to be 
   chained together without having to co-develop those models.  

    a. Specifically, if data types match between the *upstream* model and the 
       *downstream* model, the cost for data transmission is trivial.  The 
       binary-on-the-wire format used within ``acumos`` minimizes the need
       for additional serialization between textual formats like JSON.

       **NOTE**: Currently, type checking between forwarded data models is minimal.  
       Incompatible types will result in exceptions being thrown from within
       this package.  Future revisions may include more advanced error capture and
       reporting methodology.

    b. The model runner looks for the file ``runtime.json`` in the current working
       directory.  Within this file, one or more fowards to different hosts and ports
       are trivially configured.  The example below fowards to a single downstream endpoint.

        ::

            {"downstream": ["http://127.0.0.1:8887/classify"]}

    c. When the model runner is configured to send results *downstream* it will wait
       on and return the reply data from that **first downstream model**.  This data flow
       was chosen to allow callers to execute a synchronous call and get results from 
       one place (the called endpoint), regardless of how many *downstream* models
       are connected.

       To override this functionality and disable return of the results from a downstream
       instance, you can specify the argument ``--no_downstream``.

    d. To override a runtime forward file, you can specify the argument ``--no_downstream``.
       This argument will always take precedence over the existence of a foward file.
       
4. **Runtime Robustness**: Next, launch the model runner (if using *upstream* and *downstream* models, the 
   exact order does not matter).  The package will parse and load your model and then
   proceed to stand up servers in a multi-process fashion.

    a. To increase robustness to software failures, the server initialization procedure
       does employ a timeout for parsing and loading models.

    b. This timeout can be varied with the ``--timeout`` flag and an argument specifying
       a time limit in seconds.

    c. Additionally, the model runner uses a low default of concurrent processes 
       for operation.  If you find that your model is under heavy load then you can
       specify alternate instance counts with the ``--workers`` argument.
   
   
Model Runner Command Options
----------------------------

This is the primary execution script provided by the `python-model-runner` package.

```
usage: runner.py [-h] [--port PORT] [--modeldir MODELDIR] [--json_io]
                 [--return_output]

optional arguments:
  -h, --help           show this help message and exit
  --port PORT
  --modeldir MODELDIR  specify the model directory to load
  --json_io            input+output rich JSON instead of protobuf
  --return_output      return output in response instae of just downstream
```

To test JSON-based endpoints, you can specify the flag `--json_io` and the app will attempt ot decode and encode outputs in JSON.

Note that the downstream applications that are being "published" to are defined in `runtime.json` file via the `downstream` key. However, you can
also request that the output is included in the response with the flag `--return_output`.

The following examples are provided for curl-based evaluation from a command-line.
