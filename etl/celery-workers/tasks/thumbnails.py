"""
Celery Task: Thumbnail Generation

Generates video thumbnails/previews at specific timestamps
using ffmpeg.
"""

import os
import subprocess
import logging
import boto3
from typing import List
from PIL import Image

logger = logging.getLogger(__name__)


def generate_thumbnails(
    video_id: str,
    movie_id: str,
    s3_key: str,
    timestamps: List[int] = None,
    resolution: str = '1280x720'
) -> dict:
    """
    Generate thumbnails from video at specific timestamps

    Args:
        video_id: Video UUID
        movie_id: Movie UUID
        s3_key: S3 key for source video
        timestamps: List of timestamps in seconds
        resolution: Output resolution (WIDTHxHEIGHT)

    Returns:
        Dictionary with generated thumbnail URLs

    Process:
        1. Download source video from S3
        2. Extract frames at timestamps using ffmpeg
        3. Optimize images
        4. Upload to S3
        5. Update database
    """
    logger.info(f"Starting thumbnail generation for video {video_id}")

    timestamps = timestamps or [0, 300, 600, 1200, 1800]  # 0s, 5m, 10m, 20m, 30m

    try:
        # Step 1: Download source video from S3
        logger.info("Downloading source video from S3...")

        s3_client = boto3.client('s3')
        bucket_name = 'cinema-videos'

        local_video_path = f"/tmp/thumbnails/{video_id}/input.mp4"
        os.makedirs(os.path.dirname(local_video_path), exist_ok=True)

        s3_client.download_file(bucket_name, s3_key, local_video_path)
        logger.info(f"Downloaded: {local_video_path}")

        # Step 2: Extract frames at timestamps
        output_dir = f"/tmp/thumbnails/{video_id}/frames"
        os.makedirs(output_dir, exist_ok=True)

        thumbnail_files = []

        for i, timestamp in enumerate(timestamps):
            output_file = f"{output_dir}/thumbnail_{i:03d}.jpg"

            # FFmpeg command to extract frame
            ffmpeg_cmd = [
                'ffmpeg',
                '-ss', str(timestamp),  # Seek to timestamp
                '-i', local_video_path,
                '-vframes', '1',  # Extract 1 frame
                '-s', resolution,  # Resolution
                '-q:v', '2',  # Quality (2 is high quality)
                '-y',
                output_file
            ]

            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error at timestamp {timestamp}: {result.stderr}")
                continue

            # Step 3: Optimize image
            _optimize_image(output_file)

            thumbnail_files.append({
                'timestamp': timestamp,
                'file_path': output_file,
                'index': i
            })

            logger.info(f"✅ Generated thumbnail at {timestamp}s: {output_file}")

        # Step 4: Generate animated preview (GIF)
        logger.info("Generating animated preview...")
        preview_gif = _generate_animated_preview(
            local_video_path,
            output_dir,
            duration=10,
            fps=10
        )

        if preview_gif:
            thumbnail_files.append({
                'timestamp': -1,
                'file_path': preview_gif,
                'index': 999,
                'type': 'animated_preview'
            })

        # Step 5: Upload to S3
        logger.info("Uploading thumbnails to S3...")

        s3_urls = {}

        for thumb in thumbnail_files:
            filename = os.path.basename(thumb['file_path'])
            s3_thumbnail_key = f"movies/{movie_id}/thumbnails/{video_id}/{filename}"

            # Upload file
            s3_client.upload_file(
                thumb['file_path'],
                bucket_name,
                s3_thumbnail_key,
                ExtraArgs={
                    'ContentType': 'image/jpeg' if filename.endswith('.jpg') else 'image/gif',
                    'CacheControl': 'max-age=31536000'  # 1 year
                }
            )

            # Generate public URL
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_thumbnail_key}"

            s3_urls[f"thumbnail_{thumb['index']}"] = {
                'url': s3_url,
                'timestamp': thumb.get('timestamp'),
                'type': thumb.get('type', 'static')
            }

            logger.info(f"Uploaded: {s3_thumbnail_key}")

        # Step 6: Cleanup local files
        logger.info("Cleaning up local files...")
        import shutil
        shutil.rmtree(f"/tmp/thumbnails/{video_id}")

        # Step 7: Update database
        _update_thumbnail_urls(video_id, s3_urls)

        logger.info(f"✅ Thumbnail generation completed for video {video_id}")

        return {
            'video_id': video_id,
            'status': 'completed',
            'thumbnails': s3_urls,
            'count': len(thumbnail_files)
        }

    except Exception as e:
        logger.error(f"❌ Thumbnail generation failed for video {video_id}: {e}")
        raise


def _optimize_image(image_path: str):
    """
    Optimize image size and quality

    Uses PIL to compress JPEG
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Save with optimization
            img.save(
                image_path,
                'JPEG',
                quality=85,
                optimize=True,
                progressive=True
            )

        logger.debug(f"Optimized image: {image_path}")

    except Exception as e:
        logger.warning(f"Failed to optimize image {image_path}: {e}")


def _generate_animated_preview(
    video_path: str,
    output_dir: str,
    duration: int = 10,
    fps: int = 10
) -> str:
    """
    Generate animated GIF preview from video

    Args:
        video_path: Path to source video
        output_dir: Output directory
        duration: Duration of preview in seconds
        fps: Frames per second

    Returns:
        Path to generated GIF file
    """
    try:
        output_file = f"{output_dir}/preview.gif"

        # FFmpeg command to create GIF
        # Take first 10 seconds, resize to 480p, 10 fps
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', video_path,
            '-t', str(duration),  # Duration
            '-vf', f'fps={fps},scale=854:480:flags=lanczos',  # FPS and scale
            '-loop', '0',  # Loop forever
            '-y',
            output_file
        ]

        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg GIF error: {result.stderr}")
            return None

        logger.info(f"Generated animated preview: {output_file}")

        return output_file

    except Exception as e:
        logger.error(f"Failed to generate animated preview: {e}")
        return None


def _update_thumbnail_urls(video_id: str, thumbnail_urls: dict):
    """
    Update video record with thumbnail URLs

    In production, use database connection from config
    """
    logger.info(f"Updating thumbnail URLs for video {video_id}")

    # Pseudo-code for database update
    # import psycopg2
    # import json
    # conn = psycopg2.connect(DATABASE_URL)
    # cursor = conn.cursor()
    # cursor.execute(
    #     "UPDATE videos SET thumbnail_urls = %s WHERE id = %s",
    #     (json.dumps(thumbnail_urls), video_id)
    # )
    # conn.commit()

    pass
