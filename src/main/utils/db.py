import boto3
import json
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr, Equals
import botocore

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")


class DB(object):
    """A simple class to perform DB ops"""
    def __init__(
        self,
        table: str,
        ):
        self.client = dynamodb.Table(table)

    def put(self, items):
        # TODO: write code..
        try:
            clean_items = self._clean_data(items)
            resp = self.client.put_item(
                Item=clean_items,
                )
        except ClientError as e:
            print("Error writing to DB: {}".format(str(e)))
            print(clean_items)
        return resp

    def _clean_data(self, data):
        new_data = {}
        for key in data:
            if data.get(key):
                new_data.update({
                                key: data[key]
                                })
        return new_data

    def get(self, expression):
        filter_expr={}
        if expression.get("key"):
            filter_expr["KeyConditionExpression"] = getattr(Key(expression.get("key")["name"]), expression.get("condition"))(expression.get("key")["value"])
        if expression.get("attr"):
            attr_expr = expression.get("attr")
            if not attr_expr.get("value"):
                filter_expr["FilterExpression"] = getattr(Attr(attr_expr["name"]), "not_exists")()
            else:
                filter_expr["FilterExpression"] = getattr(Attr(attr_expr["name"]), attr_expr["condition"])(attr_expr["value"])
        resp = self.client.query(
                         ReturnConsumedCapacity='TOTAL',**filter_expr
                         )
        return resp.get("Items")

    def get_item(self, expression):
        return self.client.get_item(Key=expression).get("Item")

    def delete(self, expression):
        items_to_delete = self.get(expression)
        p_key, s_key = self._get_primary_key()
        resp = {}
        del_count = 0
        for item in items_to_delete:
            key_map = {
                p_key: item.get(p_key),
                s_key: item.get(s_key)
            }
        # if not expression.get("key"):
        #     log.error("you must provide partition and sort keys")
        #     return
            try:
                resp = self.client.delete_item(
                                        Key=key_map,
                                        ReturnConsumedCapacity='TOTAL'
                                        )
                del_count += 1
                print("deleted")
            except Exception:
                continue
        print("deleted {} items".format(del_count))

    def _get_primary_key(self):
        p_key, s_key = None, None
        for ks_element in self.client.key_schema:
            if ks_element.get("KeyType") == "HASH":
                p_key = ks_element.get("AttributeName")
            if ks_element.get("KeyType") == "RANGE":
                s_key = ks_element.get("AttributeName")
        return p_key, s_key


if __name__ == '__main__':
    db = DB("HacktoberIssues")
    ALL_LANG = {'HTML', 'Twig', 'CSS', 'Swift', 'Julia', 'Haskell', 'Kotlin', 'Svelte', 'HCL', 'Vue', 'TypeScript', 'Rust', 'Dockerfile', 'YAML', 'Shell', 'C++', 'C', 'Java', 'SCSS', 'Jupyter Notebook', 'R', 'Q#', 'Lua', 'C#', 'Perl', 'PHP', 'Go', 'Ruby', 'Hack', 'Cython', 'Python', 'Elixir', 'JavaScript', 'Dart'}
    for lang in ALL_LANG:
    # resp = db.get({
    #        "key": {
    #        "name": "language",
    #        "value": "Python"
    #        },
    #        "condition": "eq"
    #        })
        db.delete({
                         "key": {
                         "name": "language",
                         "value": lang
                         },
                         "condition": "eq",
                         "attr": {
                         "name": "title",
                         "value": None
                         }
                         })
