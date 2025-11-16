"""
Recommendation Event Handler

Handles recommendation events from Kafka (daily digests, personalized recommendations)
"""

import logging
from app.providers.email import EmailProvider
from app.providers.push import PushProvider
from app.providers.email.base import EmailMessage, EmailRecipient
from app.providers.push.base import PushNotification, PushRecipient

logger = logging.getLogger(__name__)


class RecommendationEventHandler:
    """
    Handler for recommendation-related events

    Events:
    - daily_digest -> Send daily recommendations email
    - personalized_recommendation -> Send personalized movie suggestions
    """

    def __init__(self, email_provider: EmailProvider, push_provider: PushProvider):
        self.email_provider = email_provider
        self.push_provider = push_provider

    async def handle_daily_digest(self, event: dict):
        """
        Handle daily_digest event

        Event format:
        {
            "event_type": "daily_digest",
            "user_id": "uuid",
            "email": "user@example.com",
            "name": "John Doe",
            "recommendations": [
                {
                    "movie_id": "uuid",
                    "title": "The Matrix",
                    "genre": "Sci-Fi",
                    "rating": 8.7,
                    "poster_url": "https://..."
                }
            ]
        }
        """
        try:
            user_email = event.get("email")
            user_name = event.get("name", "Пользователь")
            recommendations = event.get("recommendations", [])

            if not user_email:
                logger.error("Missing user email in daily_digest event")
                return

            if not recommendations:
                logger.info(f"No recommendations for user {user_email}")
                return

            # Send daily digest email
            email = EmailMessage(
                subject="Ваша ежедневная подборка фильмов",
                to=[EmailRecipient(email=user_email, name=user_name)],
                html_body=self._render_daily_digest_email(
                    user_name=user_name,
                    recommendations=recommendations
                )
            )

            response = await self.email_provider.send_email(email)

            if response.success:
                logger.info(f"✅ Daily digest sent to {user_email}")
            else:
                logger.error(f"❌ Failed to send daily digest: {response.error}")

        except Exception as e:
            logger.error(f"Error handling daily_digest: {e}")

    async def handle_personalized_recommendation(self, event: dict):
        """
        Handle personalized_recommendation event

        Sent when ML model finds a good match for user
        """
        try:
            user_email = event.get("email")
            user_name = event.get("name", "Пользователь")
            movie_title = event.get("movie_title")
            movie_genre = event.get("movie_genre")
            reason = event.get("reason", "Мы думаем, вам понравится этот фильм")
            device_token = event.get("device_token")

            if not user_email and not device_token:
                logger.error("Missing user contact info in personalized_recommendation event")
                return

            # Send push notification (more appropriate for immediate recommendations)
            if device_token:
                push = PushNotification(
                    title=f"Рекомендуем: {movie_title}",
                    body=f"{reason} - {movie_genre}",
                    recipients=[PushRecipient(device_token=device_token, user_id=event.get("user_id"))],
                    data={
                        "type": "personalized_recommendation",
                        "movie_id": event.get("movie_id")
                    },
                    image=event.get("poster_url"),
                    click_action=f"/movie/{event.get('movie_id')}"
                )

                await self.push_provider.send_push(push)
                logger.info(f"✅ Personalized recommendation push sent")

        except Exception as e:
            logger.error(f"Error handling personalized_recommendation: {e}")

    def _render_daily_digest_email(self, user_name: str, recommendations: list) -> str:
        """Render daily digest email HTML"""
        # Build recommendations HTML
        recommendations_html = ""
        for rec in recommendations[:5]:  # Limit to 5 recommendations
            recommendations_html += f"""
            <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; background: white;">
                {f'<img src="{rec.get("poster_url")}" style="width: 150px; border-radius: 5px; float: left; margin-right: 15px;">' if rec.get("poster_url") else ''}
                <h3 style="margin-top: 0;">{rec.get('title')}</h3>
                <p><span style="background: #764ba2; color: white; padding: 3px 10px; border-radius: 15px; font-size: 12px;">{rec.get('genre')}</span></p>
                <p>⭐ Рейтинг: {rec.get('rating', 'N/A')}/10</p>
                <a href="https://cinema.example.com/movie/{rec.get('movie_id')}" style="color: #667eea;">Смотреть →</a>
                <div style="clear: both;"></div>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                .content {{ padding: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📽️ Ваша ежедневная подборка</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{user_name}</strong>!</p>
                    <p>Мы подготовили для вас персональную подборку фильмов на сегодня:</p>

                    {recommendations_html}

                    <p style="text-align: center; margin-top: 30px;">
                        <a href="https://cinema.example.com/recommendations" style="display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
                            Смотреть все рекомендации
                        </a>
                    </p>
                </div>
                <div class="footer">
                    <p>Online Cinema - Ваш мир кино</p>
                    <p><a href="https://cinema.example.com/settings/notifications">Управление уведомлениями</a></p>
                </div>
            </div>
        </body>
        </html>
        """
