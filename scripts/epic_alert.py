import os
import json
import httpx

from epic_games import extract_free_games, format_expiry


STATE_FILE = "state/epic_alert_state.json"
EPIC_URL = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"titles": []}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def send_telegram_message(text, chat_id):
    bot_token = os.environ["BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    with httpx.Client(timeout=10) as client:
        resp = client.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
        )

        if resp.status_code >= 400:
            print(resp.text)
        resp.raise_for_status()


def main():
    event = os.getenv("GITHUB_EVENT_NAME")

    # Manual workflow runs also send a test confirmation.
    if event == "workflow_dispatch":
        chat_ids = os.environ["EPIC_GAMES_CHAT_IDS"].split(",")
        for chat_id in chat_ids:
            send_telegram_message(
                "🧪 *Epic Games workflow executed successfully!*",
                chat_id.strip(),
            )

    with httpx.Client(timeout=10) as client:
        resp = client.get(EPIC_URL)
        resp.raise_for_status()

    games = extract_free_games(resp.json())
    current_titles = sorted(game["title"] for game in games)
    state = load_state()

    if current_titles != state.get("titles", []):
        if games:
            lines = [
                "🎮 *Epic Games Free Games Updated!*",
                "",
                f"🎁 *{len(games)} game(s) currently free:*",
                "",
            ]

            for index, game in enumerate(games, 1):
                line = f"*{index}. {game['title']}*\n🔗 {game['url']}"
                expiry = format_expiry(game["expires_at"])
                if expiry:
                    line += f"\n⏳ Free until: {expiry}"
                lines.append(line + "\n")

            lines.append("🎉 *Happy Gaming!*")
            chat_ids = os.environ["EPIC_GAMES_CHAT_IDS"].split(",")
            for chat_id in chat_ids:
                send_telegram_message("\n".join(lines), chat_id.strip())

        state["titles"] = current_titles
        save_state(state)


if __name__ == "__main__":
    main()
