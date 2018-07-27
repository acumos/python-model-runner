# -*- coding: utf-8 -*-
# ===============LICENSE_START=======================================================
# Acumos Apache-2.0
# ===================================================================================
# Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
# ===================================================================================
# This Acumos software file is distributed by AT&T and Tech Mahindra
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END=========================================================
"""
Provides flwo teests
"""
import io
import sys
import logging
from os.path import join as path_join
from tempfile import TemporaryDirectory
import requests
from operator import eq

import pytest
import pandas as pd
import numpy as np

from acumos.session import AcumosSession
from acumos.wrapped import load_model
from acumos.modeling import Model
from multiprocessing import Process

from acumos_model_runner import runner

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _server_run(custom_app):
    custom_app.run()

@pytest.mark.flaky(reruns=5)
def test_basic_flow():
    '''Tests model wrap and load functionality'''
    def adder(x: int, y: int) -> int:
        return x + y

    # input / output "answers"
    f1_in = (1, 2)
    f1_out = (3, )
    _generic_test(adder, f1_in, f1_out)
    _generic_test(adder, f1_in, f1_out, 10)
    _generic_test(adder, f1_in, f1_out, 100)


def _generic_test(func, in_, out_, num_worker=2):
    '''Reusable wrap test routine with swappable equality functions'''
    import time

    tdir = "/tmp/model"
    with TemporaryDirectory() as tdir:
        # first create and dump the simple model to a temporary directory        
        model = Model(transform=func)
        model_name = 'my-model'
        session = AcumosSession()
        session.dump(model, model_name, tdir)  # creates model subdirectory
        
        # other params to possibly test: timeout, workers, no_downstream, json_io
        config = {"modeldir":'{}/{}'.format(tdir, model_name), "host":"127.0.0.1", 
                  "port":2685, "workers":num_worker}
        logger.info("Loading copy for wrapped model params..")
        model_copy = load_model(config['modeldir'])
        
        # launch the runner in a new process
        logger.info("Launching model in new process...")
        model_api = 'http://{}:{}/transform'.format(config['host'], config['port'])
        run_app = runner.StandaloneApplication(config, logger)
        p = Process(target=_server_run, args=(run_app,))
        p.start()
        run_app.wait_for_startup()  # prevent start-up race condition

        # grab types and craft new inputs
        TransIn = model_copy.methods['transform'].pb_input_type
        TransOut = model_copy.methods['transform'].pb_output_type
        # transform to format to transmit over the wire
        X_msg = TransIn()
        for col, field in enumerate(TransIn.DESCRIPTOR.fields):
            setattr(X_msg, field.name, in_[col])
        trans_in_bytes = X_msg.SerializeToString()
        #logger.info(trans_in_bytes)

        # post to our local runner
        logger.info("Posting to our local instance...")
        resp = requests.post(model_api, data=trans_in_bytes)
        RespOut = TransOut.FromString(resp.content)
        for col, field in enumerate(TransOut.DESCRIPTOR.fields):
            assert eq(getattr(RespOut, field.name), out_[col])

        # kill our temporary server
        p.terminate()               


if __name__ == '__main__':
    '''Test area'''
    pytest.main([__file__, ])
