from onboarder.onboard import User

def lambda_handler(event, context):
    payload = unquote(event.get("body-json"))
    user_id, email, language = payload.split("&", 2)
    user_id, email = map(get_val, [user_id, email])
    languages = list(map(get_val, language.split("&")))
    resp = User(user_id, email).insert_to_db()
    print(resp)
    response = {}
    response["statusCode"]=302
    response["headers"]={'Location': 'http://www.instacodes.net'}
    data = {}
    response["body"]=json.dumps(data)
    return response

def get_val(item):
    return item.split("=")[1]
