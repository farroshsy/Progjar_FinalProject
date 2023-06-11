import flet as ft
import json
from chat_cli import ChatClient
import os

TARGET_IP =  "127.0.0.1"
TARGET_PORT = "9999"

class ChatRoom():
    def __init__(self, page, cc, from_user, to_user):
        self.chat = ft.TextField(label="Write a message...", autofocus=True, expand=True, on_submit=self.send_click)
        self.lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        self.send = ft.IconButton(
                    icon=ft.icons.SEND_ROUNDED,
                    tooltip="Send message",
                    on_click=self.send_click,
                )

        self.page = page
        self.cc = cc
        self.from_user = from_user
        self.to_user = to_user
        self.page.pubsub.subscribe(self.on_chat)

    def send_click(self, __e__):
        if not self.chat.value:
            self.chat.error_text = "Please enter message"
            self.page.update()
        else:
            command = f"send {self.to_user} {self.chat.value}" 
            server_call = self.cc.proses(command)
            self.lv.controls.append(ft.Text(f"{self.chat.value}"))

            if "sent" in server_call:
                self.page.pubsub.send_all(self.chat.value)

            self.chat.value = ""
            self.chat.focus()
            self.page.update()

    def on_chat(self, message): 
        check_inbox = json.loads(self.cc.inbox())
        self.lv.controls.append(ft.Text(f"{check_inbox[self.from_user]}"))
        self.page.update()

menu_item_username = ft.PopupMenuItem(
    icon=ft.icons.INSERT_EMOTICON, text="")

is_login = False


def main(page):
    textfield = ft.TextField(label="Recipient", autofocus=True, expand=True)
    cc = ChatClient()
    
    def loginorregisterdialog():
        page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text(
                "Login or Register", style=ft.TextThemeStyle.TITLE_MEDIUM
            ),
            content=ft.Column([ft.Text("Do you have an account?"), ft.Text("If you don't have an account, please register")], tight=True),
            actions=[ft.ElevatedButton("Login", on_click=login), ft.ElevatedButton("Register", on_click=register)],
        )

    def register(__e__):
        page.dialog.open = False
        page.update()
        register_dialog()
        page.update()

    def login(__e__):
        page.dialog.open = False
        page.update()
        login_dialog()
        page.update()
            

    def login_dialog():
        global is_login
        page.dialog = ft.AlertDialog(
            open=not is_login,
            modal=True,
            title=ft.Text(
                "Login", style=ft.TextThemeStyle.TITLE_MEDIUM
            ),
            content=ft.Column([goback, username, password], tight=True),
            actions=[ft.ElevatedButton("Login", on_click=login_click)],
        )

    def register_dialog():
        page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text(
                "Register", style=ft.TextThemeStyle.TITLE_MEDIUM
            ),
            # already have an account
            content=ft.Column([goback,username, password, name, country], tight=True)
             
              , 
            actions=[ft.ElevatedButton("Register", on_click=register_click)],
        )

    def register_click(__e__):
        if not username.value:
            username.error_text = "Please enter username"
            username.update()
        elif not password.value:
            password.error_text = "Please enter password"
            password.update()
        elif not name.value:
            name.error_text = "Please enter name"
            name.update()
        elif not country.value:
            country.error_text = "Please enter country"
            country.update()
        else:
            register = cc.register_user(username.value, password.value, name.value, country.value)

            if "Error" in register:
                username.error_text = "Username already exist"
                username.update()
            else:
                username.value = ""
                password.value = ""
                name.value = ""
                country.value = ""
                username.error_text=""
                password.error_text =""
                name.error_text = ""
                country.error_text = ""
                page.dialog.open = False
                page.update()
                route_change("/")
                login_dialog()
                page.update()

    def login_click(__e__):
        global is_login
        if not username.value:
            username.error_text = "Please enter username"
            username.update()
        elif not password.value:
            password.error_text = "Please enter password"
            password.update()
        else:
            login = cc.login(username.value, password.value)

            if "Error" in login:
                username.error_text = "Username or Password does not match"
                password.error_text = "Username or Password does not match"
                username.update()

            else:
                menu_item_username.text = "Hello, " + username.value
                username.value = ""
                password.value = ""
                username.error_text=""
                password.error_text =""
                is_login = True
                page.dialog.open = False
                page.update()
                route_change("/")
                page.update()

    username = ft.TextField(label="Username")
    password = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        on_submit=login_click,
    )
    name = ft.TextField(label="Name")
    country = ft.TextField(label="Country")
    goback = ft.IconButton(
        icon=ft.icons.ARROW_BACK,
        tooltip="Go back",
        # close dialog, page update,loginoorregisterdialog, page update
        on_click=lambda _: [setattr(page.dialog, "open", False), page.update(), loginorregisterdialog(), page.update()],
    )

    loginorregisterdialog()   
    # register_dialog()
    # login_dialog() 

    menu = ft.PopupMenuButton(
        items=[
            menu_item_username,
        ]
    )

    def route_change(__route__):
        troute = ft.TemplateRoute(page.route)
        page.views.clear()

        page.views.append(
            ft.View(
                "/",
                [
                    menu,
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.PERSON),
                                        title=ft.Text("Private Chat"),
                                        on_click=lambda _: page.go("/private"),
                                    ),
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.GROUP),
                                        title=ft.Text("Group Chat"),
                                        on_click=lambda _: page.go("/group"),
                                    ),
                                    ft.ListTile(
                                        
                                    ),                            
                                ],
                            ),
                            padding=ft.padding.symmetric(vertical=10),
                        )
                    ),
                ],
            )
        )

        if troute.match("/private"):
            page.views.append(
                ft.View(
                    "/private",
                    [
                        ft.AppBar(title=ft.Text("Private Chat"), actions=[menu]),
                        textfield,
                        ft.ElevatedButton(
                            "Chat",
                            on_click=lambda _: page.go(f"/private/{textfield.value}"
                            ),
                        ),
                    ],
                )
            )

        elif troute.match("/private/:username"):
            cr = ChatRoom(page, cc, cc.username, troute.username)
            page.views.append(
                ft.View(
                    f"/private/{troute.username}",
                    [
                        ft.AppBar(title=ft.Text(f"Private Chat with {troute.username}"), actions=[menu]),
                        cr.lv,
                        ft.Row([cr.chat, cr.send]),
                    ],
                )
            )

        elif troute.match("/group"):
            page.views.append(
                ft.View(
                    "/group",
                    [
                        ft.AppBar(title=ft.Text("Group Chat"), actions=[menu]),
                    ],
                )
            )
        page.update()

    def view_pop(__view__):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == "__main__":
    ft.app(target=main)
