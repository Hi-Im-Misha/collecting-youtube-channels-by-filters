from googleapiclient.discovery import build
from langdetect import detect
from api_key import API_KEY

API_KEY = API_KEY

youtube = build('youtube', 'v3', developerKey=API_KEY)



config = {}
with open(r"config.txt", "r", encoding="utf-8") as f:
    for line in f:
        key, value = line.strip().split("=")
        config[key.strip()] = value.strip()

query = config.get("query", "музыка")
max_results = int(config.get("max_results"))
min_subs = int(config.get("min_subs"))
max_subs = int(config.get("max_subs"))
min_views = int(config.get("min_views"))
max_views = int(config.get("max_views"))
region_hint = config.get("region_hint")

print(f"Запрос: {query}, Макс. результатов: {max_results}, Мин. подписчиков: {min_subs}")






def search_channels(query, max_results=50):
    channels = []
    next_page_token = None

    while len(channels) < max_results:
        search_response = youtube.search().list(
            q=query,
            type='channel',
            part='snippet',
            maxResults=min(50, max_results - len(channels)),
            pageToken=next_page_token
        ).execute()

        for item in search_response['items']:
            channel_id = item['snippet']['channelId']
            channels.append(channel_id)

        next_page_token = search_response.get('nextPageToken')
        if not next_page_token:
            break

    return channels


def get_channel_data(channel_ids):
    results = []

    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i+50]
        response = youtube.channels().list(
            part='snippet,statistics',
            id=','.join(batch)
        ).execute()

        for ch in response['items']:
            snippet = ch['snippet']
            stats = ch['statistics']
            results.append({
                'title': snippet['title'],
                'channel_id': ch['id'],
                'description': snippet.get('description', ''),
                'published_at': snippet['publishedAt'],
                'subscribers': int(stats.get('subscriberCount', 0)),
                'views': int(stats.get('viewCount', 0)),
                'language_guess': snippet.get('defaultLanguage', 'unknown'),
                'country': snippet.get('country', 'unknown')
            })

    return results



def filter_channels(channels, min_subs=0, max_subs=None, min_views=0, max_views=None):
    filtered = []
    for ch in channels:
        subs = ch['subscribers']
        views = ch['views']
        country = ch['country']
        
        
        description = ch['description'].lower()
        if not description.strip():
            language = "unknown"
        else:
            try:
                language = detect(description)
            except:
                language = "unknown"



        if subs < min_subs:
            print(f"Подписчиков меньше {min_subs}")
            continue
        if max_subs is not None and subs > max_subs:
            print(f"Подписчиков больше {max_subs}")
            continue
        if views < min_views:
            print(f"Просмотров меньше {min_views}")
            continue
        if max_views is not None and views > max_views:
            print(f"Просмотров больше {max_views}")
            continue
        if region_hint and region_hint.lower() != language.lower() and region_hint.lower() != country.lower():
            print(f"Канал {ch['title']} не соответствует региону ({region_hint})")
            continue


    
        filtered.append(ch)

    return filtered

    
def save_to_txt(channels, filename=r"results.txt"):
    with open(filename, "w", encoding='utf-8') as f:
        for ch in channels:
            f.write(f"{ch['title']}\n")
            f.write(f"ID: {ch['channel_id']}\n")
            f.write(f"Дата создания: {ch['published_at']}\n")
            f.write(f"Подписчики: {ch['subscribers']}\n")
            f.write(f"Просмотры: {ch['views']}\n")
            f.write(f"Язык/регион (предположительно): {ch['language_guess']}\n")
            f.write(f"Описание: {ch['description'][:300]}...\n")
            f.write(f"Ссылка: https://www.youtube.com/channel/{ch['channel_id']}\n")
            f.write(f"Страна: {ch['country']}\n")
            f.write("-" * 60 + "\n")
            


# ==== ЗАПУСК ====
print("🔍 Поиск каналов...")
ids = search_channels(query, max_results)
print(f"Найдено каналов: {len(ids)}")

print("📥 Получение информации...")
raw_data = get_channel_data(ids)

print("🧹 Фильтрация...")
filtered = filter_channels(raw_data, min_subs, max_subs, min_views, max_views)

print(f"✅ Отобрано {len(filtered)} каналов")
save_to_txt(filtered)
print("💾 Сохранено в results.txt")