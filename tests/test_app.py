from real_estate_telegram_bot.app import App


def test_run():
    app = App("parameter")
    response = app.run("test message")
    assert response == "Message text: test message\nApp's parameter: parameter"
