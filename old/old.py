import sys
import os
import requests
import json
import re
import urllib.parse

def get_tokens():
    mainjs_url = "https://abs.twimg.com/responsive-web/client-web/main.165ee22a.js"

    mainjs = requests.get(mainjs_url)

    bearer_token = re.findall(r'AAAAAAAAA[^"]+', mainjs.text)

    assert bearer_token is not None and len(
        bearer_token) > 0, f'Failed to find bearer token.  main.js url: {mainjs_url}'

    bearer_token = bearer_token[0]
    
    # get the guest token
    with requests.Session() as s:
 
        s.headers.update({
            "user-agent"	:	"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
            "accept"	:	"*/*",
            "accept-language"	:	"de,en-US;q=0.7,en;q=0.3",
            "accept-encoding"	:	"gzip, deflate, br",
            "te"	:	"trailers",})
            
        s.headers.update({"authorization"	:	f"Bearer {bearer_token}"})

        # activate bearer token and get guest token
        guest_token = s.post(
            "https://api.twitter.com/1.1/guest/activate.json").json()["guest_token"]


    assert guest_token is not None, f'Failed to find guest token.   main.js url: {mainjs_url}'

    return bearer_token, guest_token


def get_details_url(tweet_id):

    return f"https://api.x.com/graphql/OoJd6A50cv8GsifjoOHGfg/TweetResultByRestId?variables=%7B%22tweetId%22%3A%22{tweet_id}%22%2C%22withCommunity%22%3Afalse%2C%22includePromotedContent%22%3Afalse%2C%22withVoice%22%3Afalse%7D&features=%7B%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22communities_web_enable_tweet_community_results_fetch%22%3Atrue%2C%22c9s_tweet_anatomy_moderator_badge_enabled%22%3Atrue%2C%22articles_preview_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22creator_subscriptions_quote_tweet_preview_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22rweb_video_timestamps_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D&fieldToggles=%7B%22withArticleRichContentState%22%3Atrue%2C%22withArticlePlainText%22%3Afalse%2C%22withGrokAnalyze%22%3Afalse%2C%22withDisallowedReplyControls%22%3Afalse%7D"

def get_tweet_id(tweet_url):
    tweet_id = re.findall(r'(?<=status/)\d+', tweet_url)

    assert tweet_id is not None and len(
        tweet_id) == 1, f'Could not parse tweet id from your url.  Make sure you are using the correct url. Tweet url: {tweet_url}'

    return tweet_id[0]

def get_tweet_details(tweet_id, guest_token, bearer_token):
    # tweet_id = get_tweet_id(tweet_url)

    # the url needs a url encoded version of variables and features as a query string
    url = get_details_url(tweet_id)

    details = requests.get(url, headers={
        'authorization': f'Bearer {bearer_token}',
        'x-guest-token': guest_token,
    })



    assert details.status_code == 200, f'Failed to get tweet details.'

    return details


def extract_mp4s_2(j):
    data = json.loads(j)

    mp4_urls = [
        (variant["bitrate"],variant["url"]) for variant in data["data"]["tweetResult"]["result"]["legacy"]["entities"]["media"][0]["video_info"]["variants"]
        if variant["content_type"] == "video/mp4"
    ]
    return mp4_urls


def download_video(tweet_url) :
    bearer_token, guest_token = get_tokens()

    tweet_id = get_tweet_id(tweet_url)
    resp = get_tweet_details(tweet_id, guest_token, bearer_token)

    mp4s = extract_mp4s_2(resp.text)
    print("mp4s : ", mp4s)


    for bitrate,mp4 in mp4s :
        output_file = f"{tweet_id}_{bitrate}.mp4"
        r = requests.get(mp4, stream=True)
        with open(output_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()


if __name__ == "__main__":
    #parse url from arguments
    # url should be in the form of https://twitter.com/i/status/1234567890
    tweet_url = sys.argv[1]
    download_video(tweet_url)