from bottle import route, run, template, request


@route("/", method="POST")
def index():
    current_health = request.json.get("player", {}).get("state", {}).get("health", 100)
    previous_health = request.json.get("previously", {}).get("player", {}).get("state", {}).get("health", 0)

    print(f"current health: {current_health}")
    print(f"previous health: {previous_health}")

    if current_health == 0:
        if previous_health > current_health:
            if request.json["provider"]["steamid"] == request.json["player"]["steamid"]:
                print("player has died!")

    print(request.json)

    return "test"


run(host='0.0.0.0', port=8080)
