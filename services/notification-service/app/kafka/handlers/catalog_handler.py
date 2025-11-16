"""
Catalog Event Handler

Handles catalog events from Kafka (new movies, updates)
"""

import logging
from app.providers.email import EmailProvider
from app.providers.push import PushProvider
from app.providers.email.base import EmailMessage, EmailRecipient
from app.providers.push.base import PushNotification, PushRecipient

logger = logging.getLogger(__name__)


class CatalogEventHandler:
    """
    Handler for catalog-related events

    Events:
    - movie.published -> Notify interested users
    - movie.updated -> Notify subscribers (optional)
    """

    def __init__(self, email_provider: EmailProvider, push_provider: PushProvider):
        self.email_provider = email_provider
        self.push_provider = push_provider

    async def handle_movie_published(self, event: dict):
        """
        Handle movie.published event

        Event format:
        {
            "event_type": "movie.published",
            "movie_id": "uuid",
            "title": "The Matrix",
            "genre": "Sci-Fi",
            "director": "Wachowski",
            "actors": ["Keanu Reeves"],
            "release_date": "1999-03-31",
            "description": "...",
            "poster_url": "https://...",
            "interested_users": [
                {"user_id": "uuid", "email": "user@example.com", "name": "John", "device_token": "..."}
            ]
        }

        Note: In production, fetch interested users from user-service based on:
        - Genre preferences
        - Favorite actors/directors
        - Watchlist items
        """
        try:
            movie_title = event.get("title")
            movie_genre = event.get("genre")
            movie_description = event.get("description", "")
            poster_url = event.get("poster_url")
            interested_users = event.get("interested_users", [])

            logger.info(f"Processing movie.published: {movie_title}, {len(interested_users)} interested users")

            # In production: Query user-service to find users interested in:
            # - This genre
            # - This director
            # - These actors
            # For now, use interested_users from event

            if not interested_users:
                logger.info("No interested users for this movie")
                return

            # Send notifications to interested users
            for user in interested_users:
                user_email = user.get("email")
                user_name = user.get("name", "Пользователь")
                device_token = user.get("device_token")

                # Send email
                if user_email:
                    email = EmailMessage(
                        subject=f"Новинка в каталоге: {movie_title}",
                        to=[EmailRecipient(email=user_email, name=user_name)],
                        html_body=self._render_movie_published_email(
                            user_name=user_name,
                            movie_title=movie_title,
                            movie_genre=movie_genre,
                            movie_description=movie_description,
                            poster_url=poster_url
                        )
                    )

                    response = await self.email_provider.send_email(email)

                    if response.success:
                        logger.info(f"✅ Movie notification email sent to {user_email}")
                    else:
                        logger.error(f"❌ Failed to send email: {response.error}")

                # Send push notification
                if device_token:
                    push = PushNotification(
                        title=f"Новинка: {movie_title}",
                        body=f"В каталоге появился новый фильм в жанре {movie_genre}!",
                        recipients=[PushRecipient(device_token=device_token, user_id=user.get("user_id"))],
                        data={
                            "type": "movie_published",
                            "movie_id": event.get("movie_id"),
                            "movie_title": movie_title
                        },
                        image=poster_url,
                        click_action=f"/movie/{event.get('movie_id')}"
                    )

                    await self.push_provider.send_push(push)

        except Exception as e:
            logger.error(f"Error handling movie.published: {e}")

    async def handle_movie_updated(self, event: dict):
        """
        Handle movie.updated event

        Currently just logs the event
        In production, might notify users who have movie in watchlist
        """
        try:
            movie_title = event.get("title")
            update_type = event.get("update_type", "general")

            logger.info(f"Movie updated: {movie_title}, type: {update_type}")

            # Optional: Notify users with movie in watchlist
            # For now, just log

        except Exception as e:
            logger.error(f"Error handling movie.updated: {e}")

    def _render_movie_published_email(
        self,
        user_name: str,
        movie_title: str,
        movie_genre: str,
        movie_description: str,
        poster_url: str
    ) -> str:
        """Render movie published email HTML"""
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
                .movie-poster {{ width: 100%; max-width: 300px; border-radius: 10px; margin: 20px 0; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .genre-badge {{ display: inline-block; background: #764ba2; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎬 Новинка в каталоге!</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{user_name}</strong>!</p>
                    <p>В каталоге Online Cinema появился новый фильм, который может вам понравиться:</p>

                    <h2>{movie_title}</h2>
                    <p><span class="genre-badge">{movie_genre}</span></p>

                    {f'<img src="{poster_url}" alt="{movie_title}" class="movie-poster">' if poster_url else ''}

                    <p>{movie_description[:200]}...</p>

                    <a href="https://cinema.example.com/movie/details" class="button">Смотреть сейчас</a>

                    <p style="margin-top: 30px; font-size: 14px; color: #666;">
                        Это уведомление отправлено, потому что вы подписаны на новинки в жанре {movie_genre}.
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
