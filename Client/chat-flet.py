import chatcli

import flet as ft
import os

TARGET_IP = os.getenv("SERVER_IP") or "127.0.0.1"
TARGET_PORT = os.getenv("SERVER_PORT") or "4040"
ON_WEB = os.getenv("ONWEB") or "0"

class Message():
    def __init__(self, user_name: str, text: str, message_type: str):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type


def main(page: ft.Page):
    cmd = ft.Column()
    cmd = ft.TextField()

    def btn_click(e):
        if not cmd.value:
            cmd.error_text = "masukkan command"
            page.update()
        else:
            txt = cmd.value
            lv.controls.append(ft.Text(f"command: {txt}"))
            txt = cc.proses(txt)

            lv.controls.append(ft.Text(f"result {cc.tokenid}: {txt}"))
            page.pubsub.send_all(Message(user_name=cc.tokenid, text=f"{cc.tokenid} has joined the chat.", message_type="login_message"))
            page.update()
            
            def send_message_click(e):
                if cmd.value != "":
                    page.pubsub.send_all(Message(page.session.get("user_name"), cmd.value, message_type="chat_message"))
                    cmd.value = ""
                    cmd.focus()
                    page.update()
            

    cc = chatcli.ChatClient()


    lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    cmd = ft.TextField(label="Your command")

    page.add(lv)
    page.add(cmd, ft.ElevatedButton("Send", on_click=btn_click))


if __name__=='__main__':
    if (ON_WEB=="1"):
        ft.app(target=main,view=ft.WEB_BROWSER,port=8550)
    else:
        ft.app(target=main)
