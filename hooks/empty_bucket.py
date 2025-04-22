# -*- coding: utf-8 -*-
# import logging
# from sceptre.logging import StackLoggerAdapter
from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentTypeError
from sceptre.exceptions import InvalidHookArgumentValueError

MAX_KEYS = 1000


class EmptyBucketHook(Hook):
    """
    A hook that empties an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket to empty.
        region (str): The AWS region where the bucket is located.
        profile (str): The AWS profile to use for authentication.
    """

    def __init__(self, *args, **kwargs):
        super(EmptyBucketHook, self).__init__(*args, **kwargs)
        # self.logger = StackLoggerAdapter(logging.getLogger(__name__), __name__)
        # self.logger = logging.getLogger(__name__)

    def run(self):
        """
        Empty an S3 bucket.

        :raises: InvalidHookArgumentTypeError, if argument is not a string.
        """
        # Implement the logic to empty the S3 bucket here
        if not isinstance(self.argument, dict):
            raise InvalidHookArgumentTypeError(
                "The argument must be a dict with bucket_name as a key."
            )
        bucket_name = self.argument.get("bucket_name")
        self.logger.debug("Emptying bucket {0}".format(bucket_name))
        version_enabled = self._check_if_versioning_enabled(bucket_name)
        self.logger.debug(
            "Versioning enabled is {0} for bucket {1}".format(
                version_enabled, bucket_name
            )
        )
        if version_enabled:
            self._delete_all_versions(bucket_name)
        else:
            self._delete_all_objects(bucket_name)

    def _get_bucket_versioning(self, bucket_name):
        try:
            response = self.stack.connection_manager.call(
                service="s3",
                command="get_bucket_versioning",
                kwargs={"Bucket": bucket_name},
            )
            return response.get("Status") == "Enabled"
        except Exception as exc:
            raise InvalidHookArgumentValueError(
                "Failed to get versioning status for bucket {0}: {1}".format(
                    bucket_name, str(exc)
                )
            )

    def _check_if_versioning_enabled(self, bucket_name):
        """
        Check if versioning is enabled for the S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        :return: True if versioning is enabled, False otherwise.
        """
        # Implement the logic to check if versioning is enabled here
        return self._get_bucket_versioning(bucket_name)

    def _get_bucket_objects_versions(
        self, bucket_name, key_marker=None, version_id_marker=None
    ):
        """
        Get the objects versions in the S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        :return: A list of objects versions.
        """
        try:
            if key_marker and version_id_marker:
                response = self.stack.connection_manager.call(
                    service="s3",
                    command="list_object_versions",
                    kwargs={
                        "Bucket": bucket_name,
                        "KeyMarker": key_marker,
                        "VersionIdMarker": version_id_marker,
                        "MaxKeys": MAX_KEYS,
                    },
                )
            else:
                # If no key_marker and version_id_marker are provided, get all versions
                # This is a workaround for the S3 API limitation
                # where it doesn't return all versions in one call
                response = self.stack.connection_manager.call(
                    service="s3",
                    command="list_object_versions",
                    kwargs={"Bucket": bucket_name, "MaxKeys": MAX_KEYS},
                )
            # return response.get("Versions", [])
            return response
        except Exception as exc:
            raise InvalidHookArgumentValueError(
                "Failed to get objects for bucket {0}: {1}".format(
                    bucket_name, str(exc)
                )
            )

    def _delete_batch_versions(self, bucket_name, bucket_objects):
        object_keys = []
        for object_key in bucket_objects:
            self.logger.debug(
                "Deleting object {0} from bucket {1}".format(object_key, bucket_name)
            )
            object_keys.append(
                {"Key": object_key.get("Key"), "VersionId": object_key.get("VersionId")}
            )
        response = self._delete_bucket_all_objects(bucket_name, object_keys)
        deleted = response.get("Deleted")
        errors = response.get("Errors")
        if deleted:
            self.logger.debug(
                "Deleted {0} objects from bucket {1}".format(len(deleted), bucket_name)
            )
        if errors:
            self.logger.error(
                "Failed to delete {0} objects from bucket {1}".format(
                    len(errors), bucket_name
                )
            )
            for error in errors:
                # self.logger.error("Error: {0}".format(error))
                self.logger.debug("Error: {0}".format(error))

    def _delete_all_versions(self, bucket_name):
        """
        Delete all versions of objects in the S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        """
        response = self._get_bucket_objects_versions(bucket_name)
        is_truncated = response.get("IsTruncated")
        bucket_objects = response.get("Versions", [])
        if not is_truncated and not bucket_objects:
            self.logger.debug("No objects to delete in bucket {0}".format(bucket_name))
            return
        self._delete_batch_versions(bucket_name, bucket_objects)
        while is_truncated:
            key_marker = response.get("NextKeyMarker")
            version_id_marker = response.get("NextVersionIdMarker")
            response = self._get_bucket_objects_versions(
                bucket_name, key_marker=key_marker, version_id_marker=version_id_marker
            )
            bucket_objects = response.get("Versions", [])
            self._delete_batch_versions(bucket_name, bucket_objects)
            is_truncated = response.get("IsTruncated")

    def _get_bucket_objects(self, bucket_name, continuation_token=None):
        """
        Get the objects in the S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        :return: A list of objects.
        """
        try:
            if continuation_token:
                response = self.stack.connection_manager.call(
                    service="s3",
                    command="list_objects_v2",
                    kwargs={
                        "Bucket": bucket_name,
                        "MaxKeys": MAX_KEYS,
                        "ContinuationToken": continuation_token,
                    },
                )
            else:
                response = self.stack.connection_manager.call(
                    service="s3",
                    command="list_objects_v2",
                    kwargs={"Bucket": bucket_name, "MaxKeys": MAX_KEYS},
                )
            return response
        except Exception as exc:
            raise InvalidHookArgumentValueError(
                "Failed to get objects for bucket {0}: {1}".format(
                    bucket_name, str(exc)
                )
            )

    def _delete_bucket_all_objects(self, bucket_name, object_keys):
        """
        Delete all objects in the S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        """
        # Implement the logic to delete all objects here
        try:
            response = self.stack.connection_manager.call(
                service="s3",
                command="delete_objects",
                kwargs={"Bucket": bucket_name, "Delete": {"Objects": object_keys}},
            )
            return response
        except Exception as exc:
            raise InvalidHookArgumentValueError(
                "Failed to get versioning status for bucket {0}: {1}".format(
                    bucket_name, str(exc)
                )
            )

    def _delete_batch_objects(self, bucket_name, bucket_objects):
        object_keys = []
        for object_key in bucket_objects:
            self.logger.debug(
                "Deleting object {0} from bucket {1}".format(object_key, bucket_name)
            )
            object_keys.append({"Key": object_key.get("Key")})
        response = self._delete_bucket_all_objects(bucket_name, object_keys)
        deleted = response.get("Deleted")
        errors = response.get("Errors")
        if deleted:
            self.logger.debug(
                "Deleted {0} objects from bucket {1}".format(len(deleted), bucket_name)
            )
        if errors:
            self.logger.error(
                "Failed to delete {0} objects from bucket {1}".format(
                    len(errors), bucket_name
                )
            )
            for error in errors:
                # self.logger.error("Error: {0}".format(error))
                self.logger.debug("Error: {0}".format(error))

    def _delete_all_objects(self, bucket_name):
        """
        Delete all objects in the S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        """
        response = self._get_bucket_objects(bucket_name)
        if response.get("KeyCount") == 0:
            self.logger.debug("No objects to delete in bucket {0}".format(bucket_name))
            return
        bucket_objects = response.get("Contents", [])
        self._delete_batch_objects(bucket_name, bucket_objects)
        is_truncated = response.get("IsTruncated")
        while is_truncated:
            continuation_token = response.get("NextContinuationToken")
            response = self._get_bucket_objects(
                bucket_name, continuation_token=continuation_token
            )
            bucket_objects = response.get("Contents", [])
            self._delete_batch_objects(bucket_name, bucket_objects)
            is_truncated = response.get("IsTruncated")
