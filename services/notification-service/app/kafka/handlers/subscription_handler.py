"""
Subscription Event Handler

Handles user subscription events from Kafka
"""

import logging
from app.providers.email import EmailProvider
from app.providers.push import PushProvider
from app.providers.email.base import EmailMessage, EmailRecipient
from app.providers.push.base import PushNotification, PushRecipient

logger = logging.getLogger(__name__)


class SubscriptionEventHandler:
    """
    Handler for subscription-related events

    Events:
    - subscription.created -> Welcome email
    - subscription.expired -> Expiry notification
    - subscription.renewed -> Renewal confirmation
    """

    def __init__(self, email_provider: EmailProvider, push_provider: PushProvider):
        self.email_provider = email_provider
        self.push_provider = push_provider

    async def handle_subscription_created(self, event: dict):
        """
        Handle subscription.created event

        Event format:
        {
            "event_type": "subscription.created",
            "user_id": "uuid",
            "email": "user@example.com",
            "name": "John Doe",
            "plan_id": "premium",
            "plan_name": "Premium",
            "expires_at": "2024-12-16T10:00:00Z",
            "payment_id": "uuid"
        }
        """
        try:
            user_email = event.get("email")
            user_name = event.get("name", "Пользователь")
            plan_name = event.get("plan_name", "подписка")
            expires_at = event.get("expires_at")

            if not user_email:
                logger.error("Missing user email in subscription.created event")
                return

            # Send welcome email
            email = EmailMessage(
                subject=f"Добро пожаловать в Online Cinema! Подписка {plan_name} активирована",
                to=[EmailRecipient(email=user_email, name=user_name)],
                html_body=self._render_subscription_created_email(
                    user_name=user_name,
                    plan_name=plan_name,
                    expires_at=expires_at
                )
            )

            response = await self.email_provider.send_email(email)

            if response.success:
                logger.info(f"✅ Welcome email sent to {user_email}")
            else:
                logger.error(f"❌ Failed to send welcome email: {response.error}")

            # Send push notification (if device token available)
            device_token = event.get("device_token")
            if device_token:
                push = PushNotification(
                    title="Подписка активирована!",
                    body=f"Ваша подписка {plan_name} успешно активирована. Наслаждайтесь просмотром!",
                    recipients=[PushRecipient(device_token=device_token, user_id=event.get("user_id"))],
                    data={"type": "subscription_created", "plan_id": event.get("plan_id")}
                )

                await self.push_provider.send_push(push)

        except Exception as e:
            logger.error(f"Error handling subscription.created: {e}")

    async def handle_subscription_expired(self, event: dict):
        """
        Handle subscription.expired event

        Event format:
        {
            "event_type": "subscription.expired",
            "user_id": "uuid",
            "email": "user@example.com",
            "name": "John Doe",
            "plan_id": "premium",
            "expired_at": "2024-12-16T10:00:00Z"
        }
        """
        try:
            user_email = event.get("email")
            user_name = event.get("name", "Пользователь")
            plan_name = event.get("plan_name", "подписка")

            if not user_email:
                logger.error("Missing user email in subscription.expired event")
                return

            # Send expiry email
            email = EmailMessage(
                subject="Ваша подписка на Online Cinema истекла",
                to=[EmailRecipient(email=user_email, name=user_name)],
                html_body=self._render_subscription_expired_email(
                    user_name=user_name,
                    plan_name=plan_name
                )
            )

            response = await self.email_provider.send_email(email)

            if response.success:
                logger.info(f"✅ Expiry email sent to {user_email}")
            else:
                logger.error(f"❌ Failed to send expiry email: {response.error}")

            # Send push notification
            device_token = event.get("device_token")
            if device_token:
                push = PushNotification(
                    title="Подписка истекла",
                    body="Ваша подписка на Online Cinema закончилась. Продлите сейчас!",
                    recipients=[PushRecipient(device_token=device_token, user_id=event.get("user_id"))],
                    data={"type": "subscription_expired", "plan_id": event.get("plan_id")},
                    click_action="/subscription/renew"
                )

                await self.push_provider.send_push(push)

        except Exception as e:
            logger.error(f"Error handling subscription.expired: {e}")

    async def handle_subscription_renewed(self, event: dict):
        """Handle subscription.renewed event"""
        try:
            user_email = event.get("email")
            user_name = event.get("name", "Пользователь")
            plan_name = event.get("plan_name", "подписка")
            expires_at = event.get("expires_at")

            if not user_email:
                logger.error("Missing user email in subscription.renewed event")
                return

            # Send renewal email
            email = EmailMessage(
                subject=f"Подписка {plan_name} продлена",
                to=[EmailRecipient(email=user_email, name=user_name)],
                html_body=f"""
                <h1>Подписка продлена!</h1>
                <p>Здравствуйте, {user_name}!</p>
                <p>Ваша подписка <strong>{plan_name}</strong> успешно продлена.</p>
                <p>Действует до: {expires_at}</p>
                <p>Спасибо за то, что остаётесь с нами!</p>
                """
            )

            await self.email_provider.send_email(email)
            logger.info(f"✅ Renewal email sent to {user_email}")

        except Exception as e:
            logger.error(f"Error handling subscription.renewed: {e}")

    def _render_subscription_created_email(self, user_name: str, plan_name: str, expires_at: str) -> str:
        """Render welcome email HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎬 Добро пожаловать в Online Cinema!</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{user_name}</strong>!</p>
                    <p>Ваша подписка <strong>{plan_name}</strong> успешно активирована!</p>
                    <p>Теперь вы можете наслаждаться неограниченным просмотром тысяч фильмов и сериалов в HD качестве.</p>
                    <p><strong>Действует до:</strong> {expires_at}</p>
                    <a href="https://cinema.example.com/browse" class="button">Начать просмотр</a>
                    <h3>Что доступно в вашей подписке:</h3>
                    <ul>
                        <li>✨ Тысячи фильмов и сериалов</li>
                        <li>🎥 HD качество</li>
                        <li>📱 Просмотр на любых устройствах</li>
                        <li>🚫 Без рекламы</li>
                        <li>⬇️ Скачивание для офлайн-просмотра</li>
                    </ul>
                    <p>Приятного просмотра!</p>
                </div>
                <div class="footer">
                    <p>Online Cinema - Ваш мир кино</p>
                    <p>Это автоматическое письмо, пожалуйста, не отвечайте на него.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _render_subscription_expired_email(self, user_name: str, plan_name: str) -> str:
        """Render expiry email HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ff6b6b; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Подписка истекла</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{user_name}</strong>!</p>
                    <p>К сожалению, ваша подписка <strong>{plan_name}</strong> закончилась.</p>
                    <p>Продлите подписку, чтобы продолжить наслаждаться любимыми фильмами и сериалами!</p>
                    <a href="https://cinema.example.com/subscription/renew" class="button">Продлить подписку</a>
                    <h3>При продлении вы получите:</h3>
                    <ul>
                        <li>🎁 Скидка 10% на первый месяц</li>
                        <li>✨ Полный доступ ко всему контенту</li>
                        <li>🎥 HD качество без ограничений</li>
                    </ul>
                    <p>Не упустите возможность вернуться к любимым фильмам!</p>
                </div>
                <div class="footer">
                    <p>Online Cinema - Ваш мир кино</p>
                </div>
            </div>
        </body>
        </html>
        """
