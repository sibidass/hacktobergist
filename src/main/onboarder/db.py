import boto3

dynamodb = boto3.resource("dynamodb")


class DB(object):
    """A simple class to perform DB ops"""
    def __init__(
        self,
        table: str,
        ):
        self.client = dynamodb.Table(table)

    def put(self, items):
        # TODO: write code..
        resp = self.client.put_item(
            Item=self._clean_data(items),
            )
        return resp

    def _clean_data(self, data):
        for key in data:
            if not data.get(key):
                data.pop(key)
        return data
