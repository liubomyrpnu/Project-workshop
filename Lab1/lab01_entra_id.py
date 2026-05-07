import requests
from azure.identity import DefaultAzureCredential

DOMAIN = "dumenchuklubgmail.onmicrosoft.com"
GUEST_EMAIL = "liubomyr.dumenchuk.23@pnu.edu.ua"

def get_graph_headers():
    credential = DefaultAzureCredential()
    token = credential.get_token('https://graph.microsoft.com/.default').token
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


def main():
    headers = get_graph_headers()

    print("\n1. Створюємо користувача...")

    user_payload = {
        "accountEnabled": True,
        "displayName": "az104-user1",
        "mailNickname": "az104-user1",
        "userPrincipalName": f"az104-user1@{DOMAIN}",
        "passwordProfile": {
            "forceChangePasswordNextSignIn": False,
            "password": "StrongP@ssw0rd2026!"
        },
        "jobTitle": "IT Lab Administrator",
        "department": "IT",
        "usageLocation": "US"
    }

    response = requests.post(
        'https://graph.microsoft.com/v1.0/users',
        headers=headers,
        json=user_payload
    )

    if response.status_code == 201:
        user1_id = response.json()['id']
        print(f"✅ Користувача створено! ID: {user1_id}")
    else:
        print(f"❌ Помилка створення користувача:\n{response.text}")
        return

    print(f"\n2. Запрошуємо Guest: {GUEST_EMAIL}...")

    invite_payload = {
        "invitedUserEmailAddress": GUEST_EMAIL,
        "inviteRedirectUrl": "https://portal.azure.com",
        "sendInvitationMessage": True
    }

    invite_response = requests.post(
        'https://graph.microsoft.com/v1.0/invitations',
        headers=headers,
        json=invite_payload
    )

    if invite_response.status_code == 201:
        guest_id = invite_response.json()['invitedUser']['id']
        print(f"✅ Guest створено! ID: {guest_id}")
    else:
        print(f"❌ Помилка запрошення:\n{invite_response.text}")
        return

    print("\n3. Створюємо групу...")

    group_payload = {
        "displayName": "IT Lab Administrators",
        "mailEnabled": False,
        "mailNickname": "ITLabAdmins",
        "securityEnabled": True,
        "description": "Administrators that manage the IT lab"
    }

    group_response = requests.post(
        'https://graph.microsoft.com/v1.0/groups',
        headers=headers,
        json=group_payload
    )

    if group_response.status_code == 201:
        group_id = group_response.json()['id']
        print(f"✅ Групу створено! ID: {group_id}")
    else:
        print(f"❌ Помилка створення групи:\n{group_response.text}")
        return

    print("\n4. Додаємо користувачів у групу...")

    for uid in [user1_id, guest_id]:
        member_payload = {
            "@odata.id": f"https://graph.microsoft.com/v1.0/users/{uid}"
        }

        add_response = requests.post(
            f'https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref',
            headers=headers,
            json=member_payload
        )

        if add_response.status_code == 204:
            print(f"✅ Додано користувача {uid}")
        else:
            print(f"❌ Помилка додавання:\n{add_response.text}")

    print("\n🎉 ГОТОВО! Лабораторна виконана")


if __name__ == "__main__":
    main()