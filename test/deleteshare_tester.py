import time
import test.fake_3par_data as data
import test.hpe_docker_unit_test as hpedockerunittest
import copy

from oslo_config import cfg
CONF = cfg.CONF


class DeleteShareUnitTest(hpedockerunittest.HpeDockerUnitTestExecutor):
    def _get_plugin_api(self):
        return 'volumedriver_remove'

    def override_configuration(self, all_configs):
        pass


class TestDeleteShare(DeleteShareUnitTest):

    def __init__(self, test_obj):
        self._test_obj = test_obj

    def get_request_params(self):
        return self._test_obj.get_request_params()

    def setup_mock_objects(self):
        self._test_obj.setup_mock_objects(self.mock_objects)

    def check_response(self, resp):
        self._test_obj.check_response(resp, self.mock_objects,
                                      self._test_case)

    # Nested class to handle regular volume
    class Regular(object):
        def __init__(self, params={}):
            self._params = params

        def get_request_params(self):
            share_name = 'MyDefShare_01'
            return {"Name": share_name,
                    "Opts": {}}

        def setup_mock_objects(self, mock_objects):
            mock_share_etcd = mock_objects['mock_share_etcd']
            if 'share_with_acl' in self._params:
                mock_share_etcd.get_share.return_value = copy.deepcopy(
                    data.etcd_share_with_acl)
            else:
                mock_share_etcd.get_share.return_value = copy.deepcopy(
                    data.etcd_share)
            mock_file_client = mock_objects['mock_file_client']
            mock_file_client.http.get.side_effect = [
                # This file store is deleted as part of share delete
                (data.get_fstore_resp, data.get_fstore_body),
                # No more file store present on parent FPG
                (data.get_fstore_resp, data.no_fstore_body),
                # WSAPI for FPG delete requires ID of FPG for which
                # FPG is being fetched by name
                (data.get_bkend_fpg_resp, data.bkend_fpg)
            ]
            mock_fp_etcd = mock_objects['mock_fp_etcd']
            # ETCD having FPG metadata means the host owns the FPG
            # Since last share on the FPG got deleted, FPG also needs
            # to be deleted
            mock_fp_etcd.get_fpg_metadata.return_value = \
                data.etcd_bkend_mdata_with_default_fpg

            mock_file_client.http.delete.return_value = \
                (data.fpg_delete_task_resp, data.fpg_delete_task_body)

            mock_file_client.getTask.return_value = data.fpg_delete_task_body
            mock_file_client.TASK_DONE = 1

        def check_response(self, resp, mock_objects, test_case):
            # Check if these functions were actually invoked
            # in the flow or not
            mock_3parclient = mock_objects['mock_3parclient']
            mock_3parclient.getWsApiVersion.assert_called()
            time.sleep(3)

            # mock_3parclient.deleteVolume.assert_called()
            #
            # mock_etcd = mock_objects['mock_etcd']
            # mock_etcd.delete_vol.assert_called()
