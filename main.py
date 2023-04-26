import requests
import vk_api
import psycopg2
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.exceptions import ApiError

with open('token.txt') as file:
    token_bot = file.readline()
    token_vk = file.readline()
vk_session = vk_api.VkApi(token=token_bot)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()
vk_tok = vk_api.VkApi(token=token_vk)


def send_msg(chat_id, message):
    vk.messages.send(chat_id=chat_id, message=message, random_id=0)


def send_photo(chat_id, attachment):
    vk.messages.send(chat_id=chat_id, attachment=attachment, random_id=0)


def get_user_info(user_id):
    url = "https://api.vk.com/method/users.get"
    params = {
        "access_token": token_vk,
        "user_ids": user_id,
        "v": "5.131",
        "fields": "bdate, sex, city, relation"
    }
    res = requests.get(url, params).json()
    age = 2023 - int(res["response"][0]["bdate"].split(".")[2])
    city_id = 1# res["response"][0]["city"]["id"]
    sex = res["response"][0]["sex"]
    if sex == 2:
        sex = 1
    return city_id, age, sex


def search(user_info_tuple: tuple, offset=None):
    try:
        profiles = vk_tok.method("users.search",
                                 {"city_id": user_info_tuple[0],
                                  "age_from": user_info_tuple[1],
                                  "age_to": user_info_tuple[1],
                                  "sex": user_info_tuple[2],
                                  "count": 10,
                                  "offset": offset
                                  })
    except ApiError:
        return
    profiles = profiles["items"]
    user_id_list = []
    for profile in profiles:
        if not profile["is_closed"]:
            user_id_list.append({"name": profile["first_name"] + " " + profile["last_name"],
                                 "id": profile["id"]
                                 })
    return user_id_list


def photos_get(user_id):
    photos = vk_tok.method("photos.get",
                           {"album_id": "profile",
                            "owner_id": user_id
                            }
                           )
    try:
        photos = photos["items"]
    except KeyError:
        return

    user_photo_list = []
    for num, photo in enumerate(photos):
        user_photo_list.append({"owner_id": photo["owner_id"],
                                "id": photo["id"]
                                })
        if num == 3:
            break
    return user_photo_list


def write_db(user_id):
    with psycopg2.connect(database="vkinder", user="postgres", password="7") as conn:
        cur = conn.cursor()
        cur.execute("""
                CREATE TABLE IF NOT EXISTS users_id(
                id SERIAL PRIMARY KEY,
                user_vk_id INTEGER NOT NULL UNIQUE
                );
                """)
        cur.execute("SELECT user_vk_id FROM users_id WHERE user_vk_id = %s", (user_id,))
        answer = cur.fetchone()
        if answer is None:
            cur.execute("INSERT INTO users_id(user_vk_id) VALUES (%s)", (user_id,))
            conn.commit()


# chat
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
        if event.text.lower() == "привет" or event.text.lower() == "ghbdtn":
            send_msg(event.chat_id, "Привет, сейчас все будет!")
        elif event.text.lower() == "поиск" or event.text.lower() == "gjbcr":
            send_msg(event.chat_id, "Нашли:")
            find_user_info = get_user_info(event.user_id)
            list_more_users = search(find_user_info)
            while len(list_more_users) > 0:
                item_user_id = list_more_users.pop(-1)["id"]
                write_db(item_user_id)
                photo_user_dict = photos_get(item_user_id)
                for item in photo_user_dict:
                    photo_data_owner_id = item["owner_id"]
                    photo_data_user_id = item["id"]
                    send_photo(event.chat_id, f"photo{photo_data_owner_id}_{photo_data_user_id}")
        else:
            send_msg(event.chat_id, "Неверная команда")
