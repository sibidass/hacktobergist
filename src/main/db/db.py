import boto3
import sys

dynamo = boto3.client("dynamodb", region_name="us-west-2")

data_type_map = {
    type('str'): 'S',
    type(2): 'N',
    type([]): 'L',
    type({}): 'M'
}

def get_db_dtype(record):
    formatted_item = {}
    for item in record:
        if data_type_map.get(type(record[item])) == 'M':
            formatted_item.update({item:{ 'M': get_db_dtype(record[item])}})
        elif data_type_map.get(type(record[item])) == 'L':
            formatted_item.update({item:{ 'L': [{data_type_map.get(type(x)): x} for x in record[item]]}})
        else:
            formatted_item.update({
                                    item: { data_type_map.get(type(record[item])): str(record[item])}
                                  })
    return formatted_item

class DataBase(object):
    """docstring for DataBase"""
    def __init__(self, dbname):
        self.dbname = dbname
        self.p_key = None
        self.s_key = None
        self.__set_pkeys()

    def __set_pkeys(self):
        resp = dynamo.describe_table(
                                    TableName=self.dbname
                                   )
        schema = resp.get('Table')['KeySchema']
        for item in schema:
            if item.get('KeyType') == 'HASH':
                self.p_key = item.get('AttributeName')
            elif item.get('KeyType') == 'RANGE':
                self.s_key = item.get('AttributeName')

    def insert(self, record):
        db_formatted_item = get_db_dtype(record)
        dynamo.put_item(
                                TableName=self.dbname,
                                Item=db_formatted_item
                             )

    def scan(self, attributes, limit=sys.maxsize, items_only=True, **kwargs):
        data = []
        query_params = {
            "TableName": self.dbname,
            "ProjectionExpression": attributes
        }
        if kwargs:
            print("adding additional attributes to query")
            query_params.update(kwargs)
        while True:
            resp = dynamo.scan(**query_params)
            if items_only:
                data.extend(resp.get("Items"))
            else:
                data.append(resp)
            if not resp.get("LastEvaluatedKey") or len(data) >= limit:
                break
            query_params.update(
                                {
                                    "ExclusiveStartKey": resp.get("LastEvaluatedKey")
                                }
                                )
        return data

    def get(self, pkey_val, attributes):
        query_params = {
            "TableName": self.dbname,
            "ProjectionExpression": attributes,
            "Key": {
                self.p_key: {
                    'S': pkey_val
                }
            }
        }
        resp = boto_client.get_item(**query_params)
        return resp.get("Item")
