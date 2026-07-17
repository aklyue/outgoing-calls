import os
import uuid
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from ldap3 import Server, Connection, ALL, SUBTREE
import ssl

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-for-dev-only")
ALGORITHM = "HS256"
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

LDAP_SERVER = os.getenv("LDAP_SERVER", "ldap://dc2.ssga.local:389")
LDAP_DOMAIN = os.getenv("LDAP_DOMAIN", "ssga.local")
LDAP_USER_BASE = os.getenv(
    "LDAP_USER_BASE", "OU=Административная часть Университета,DC=ssga,DC=local"
)
LDAP_GROUP_DN = os.getenv(
    "LDAP_GROUP_DN",
    "CN=Доступ к службе обзвона,OU=Приемная комиссия,OU=Административная часть Университета,DC=ssga,DC=local",
)

LDAP_UUID = os.getenv("LDAP_UUID", "ee25229d-30ea-4d43-957d-a4373de0202b")


def verify_ldap_auth(username: str, password: str) -> bool:
    """
    Проверяет пароль в AD. Находит группу по её UUID и проверяет,
    содержится ли она в списке групп пользователя.
    """
    user_principal = username 
    
    try:
        server = Server(LDAP_SERVER, get_info=ALL, connect_timeout=20)
        
        with Connection(server, user=user_principal, password=password, auto_referrals=False) as conn:
            
            print(f"DEBUG: Пробую авторизацию как {user_principal}")
            if not conn.bind():
                print(f"DEBUG: AD rejected bind for {user_principal}. Результат: {conn.result}")
                return False

            print(f"✅ УСПЕХ: Авторизация пройдена!")

            # 1. Сначала ищем группу ПО ЕЁ UUID из .env
            target_uuid = LDAP_UUID.lower()
            
            # ВАЖНО: Используем bytes_le для конвертации в формат Microsoft Active Directory
            target_bytes_le = uuid.UUID(target_uuid).bytes_le
            
            # Генерируем правильный экранированный фильтр (\9d\22\25...)
            guid_filter = "".join([f"\\{b:02x}" for b in target_bytes_le])
            group_filter = f"(objectGUID={guid_filter})"

            # ИСПРАВЛЕНИЕ ТУТ: убрали attributes=['dn'], чтобы не ловить ошибку!
            conn.search(
                search_base="DC=ssga,DC=local", 
                search_filter=group_filter, 
                search_scope=SUBTREE
            )

            if not conn.entries:
                print(f"DEBUG: Группа с UUID {target_uuid} не найдена в AD.")
                return False

            # Получаем точный DN группы
            target_group_dn = conn.entries[0].entry_dn
            print(f"DEBUG: Найдена группа: {target_group_dn}")

            # 2. Ищем пользователя и запрашиваем список ЕГО групп (атрибут memberOf)
            search_filter = f"(userPrincipalName={username})"
            conn.search(
                search_base="DC=ssga,DC=local", 
                search_filter=search_filter, 
                search_scope=SUBTREE,
                attributes=['memberOf']
            )
            
            if not conn.entries:
                print(f"DEBUG: Пользователь с UPN {username} не найден в AD.")
                return False
            
            user_entry = conn.entries[0]
            user_groups = user_entry.memberOf.values if 'memberOf' in user_entry else []
            
            user_groups_lower = [g.lower() for g in user_groups]
            
            print(f"DEBUG: Всего групп у пользователя: {len(user_groups)}")

            # 3. Эквивалент проверки user.isMemberOf(uuid)
            if target_group_dn.lower() in user_groups_lower:
                print(f"DEBUG: Доступ разрешен по методу isMemberOf! Пользователь состоит в группе.")
                return True
            else:
                print(f"DEBUG: Отказ. Пользователь не состоит в группе с UUID {target_uuid}")
                return False
        
    except Exception as e:
        print(f"LDAP Connection Error: {e}")
        return False


def hash_password(password: str):
    return pwd.hash(password[:72])


def verify_password(password: str, hashed: str):
    return pwd.verify(password[:72], hashed)


def create_access_token(data: dict, expires_minutes: int = 21600):
    to_encode = data.copy()
    now = datetime.utcnow()
    to_encode.update({"exp": now + timedelta(minutes=expires_minutes), "iat": now})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
