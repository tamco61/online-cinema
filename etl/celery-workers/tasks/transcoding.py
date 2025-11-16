"""
Celery Task: Video Transcoding

Transcodes video files to HLS/DASH formats using ffmpeg
for adaptive bitrate streaming.
"""

import os
import subprocess
import logging
from celery import Task
import boto3
from typing import List, Dict

logger = logging.getLogger(__name__)


class TranscodingTask(Task):
    """
    Base task for video transcoding with progress tracking
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        # Update database status to failed
        # Send notification

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {task_id} completed successfully")
        # Update database status to completed
        # Send notification


def transcode_video(
    video_id: str,
    movie_id: str,
    s3_key: str,
    original_file_path: str,
    output_formats: List[str] = None,
    resolutions: List[str] = None
) -> Dict:
    """
    Transcode video to multiple formats and resolutions

    Args:
        video_id: Video UUID
        movie_id: Movie UUID
        s3_key: S3 key for source video
        original_file_path: Local path or S3 path
        output_formats: List of output formats (hls, dash)
        resolutions: List of resolutions (1080p, 720p, 480p, 360p)

    Returns:
        Dictionary with transcoding results

    Process:
        1. Download source video from S3
        2. Transcode to multiple resolutions
        3. Generate HLS/DASH manifests
        4. Upload to S3
        5. Update database
    """
    logger.info(f"Starting transcoding for video {video_id}")

    output_formats = output_formats or ['hls']
    resolutions = resolutions or ['1080p', '720p', '480p', '360p']

    try:
        # Step 1: Download source video from S3
        logger.info("Downloading source video from S3...")
        s3_client = boto3.client('s3')
        bucket_name = 'cinema-videos'  # From config

        local_input_path = f"/tmp/videos/{video_id}/input.mp4"
        os.makedirs(os.path.dirname(local_input_path), exist_ok=True)

        s3_client.download_file(bucket_name, s3_key, local_input_path)
        logger.info(f"Downloaded: {local_input_path}")

        # Step 2: Transcode to multiple resolutions
        output_dir = f"/tmp/videos/{video_id}/output"
        os.makedirs(output_dir, exist_ok=True)

        transcoded_files = {}

        for resolution in resolutions:
            logger.info(f"Transcoding to {resolution}...")

            # Resolution mapping
            resolution_map = {
                '1080p': {'height': 1080, 'bitrate': '5000k'},
                '720p': {'height': 720, 'bitrate': '2500k'},
                '480p': {'height': 480, 'bitrate': '1000k'},
                '360p': {'height': 360, 'bitrate': '500k'},
            }

            res_config = resolution_map[resolution]
            output_file = f"{output_dir}/{resolution}.mp4"

            # FFmpeg command for transcoding
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', local_input_path,
                '-c:v', 'libx264',  # H.264 codec
                '-preset', 'medium',
                '-crf', '23',
                '-vf', f"scale=-2:{res_config['height']}",
                '-b:v', res_config['bitrate'],
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-y',
                output_file
            ]

            # Execute ffmpeg
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"Transcoding failed for {resolution}")

            transcoded_files[resolution] = output_file
            logger.info(f"✅ Transcoded {resolution}: {output_file}")

        # Step 3: Generate HLS playlists
        if 'hls' in output_formats:
            logger.info("Generating HLS manifests...")

            hls_dir = f"{output_dir}/hls"
            os.makedirs(hls_dir, exist_ok=True)

            # Create master playlist
            master_playlist = _generate_hls_master_playlist(
                video_id,
                transcoded_files,
                hls_dir
            )

            transcoded_files['hls_master'] = master_playlist

        # Step 4: Generate DASH manifests
        if 'dash' in output_formats:
            logger.info("Generating DASH manifests...")

            dash_dir = f"{output_dir}/dash"
            os.makedirs(dash_dir, exist_ok=True)

            dash_manifest = _generate_dash_manifest(
                video_id,
                transcoded_files,
                dash_dir
            )

            transcoded_files['dash_manifest'] = dash_manifest

        # Step 5: Upload to S3
        logger.info("Uploading transcoded files to S3...")

        s3_output_keys = {}

        for resolution, file_path in transcoded_files.items():
            s3_output_key = f"movies/{movie_id}/videos/{video_id}/{resolution}/{os.path.basename(file_path)}"

            # Upload file
            s3_client.upload_file(
                file_path,
                bucket_name,
                s3_output_key,
                ExtraArgs={'ContentType': _get_content_type(file_path)}
            )

            s3_output_keys[resolution] = s3_output_key
            logger.info(f"Uploaded: {s3_output_key}")

        # Step 6: Cleanup local files
        logger.info("Cleaning up local files...")
        import shutil
        shutil.rmtree(f"/tmp/videos/{video_id}")

        # Step 7: Update database
        _update_video_status(video_id, 'completed', s3_output_keys)

        logger.info(f"✅ Transcoding completed for video {video_id}")

        return {
            'video_id': video_id,
            'status': 'completed',
            'output_files': s3_output_keys,
            'resolutions': list(resolutions),
            'formats': list(output_formats)
        }

    except Exception as e:
        logger.error(f"❌ Transcoding failed for video {video_id}: {e}")

        # Update database status to failed
        _update_video_status(video_id, 'failed', error=str(e))

        raise


def _generate_hls_master_playlist(video_id: str, transcoded_files: Dict, output_dir: str) -> str:
    """
    Generate HLS master playlist

    Returns:
        Path to master playlist file
    """
    # Generate HLS segments for each resolution
    for resolution, mp4_file in transcoded_files.items():
        if resolution.endswith('p'):
            segment_dir = f"{output_dir}/{resolution}"
            os.makedirs(segment_dir, exist_ok=True)

            # FFmpeg command to create HLS segments
            hls_cmd = [
                'ffmpeg',
                '-i', mp4_file,
                '-c', 'copy',
                '-hls_time', '10',  # 10 second segments
                '-hls_list_size', '0',
                '-hls_segment_filename', f"{segment_dir}/segment_%03d.ts",
                '-f', 'hls',
                f"{segment_dir}/playlist.m3u8"
            ]

            subprocess.run(hls_cmd, capture_output=True, check=True)

    # Create master playlist
    master_playlist_path = f"{output_dir}/master.m3u8"

    bandwidth_map = {
        '1080p': 5000000,
        '720p': 2500000,
        '480p': 1000000,
        '360p': 500000,
    }

    with open(master_playlist_path, 'w') as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n\n")

        for resolution in sorted(transcoded_files.keys()):
            if resolution.endswith('p'):
                bandwidth = bandwidth_map.get(resolution, 1000000)
                height = int(resolution.replace('p', ''))

                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={int(height*16/9)}x{height}\n")
                f.write(f"{resolution}/playlist.m3u8\n\n")

    logger.info(f"Generated HLS master playlist: {master_playlist_path}")

    return master_playlist_path


def _generate_dash_manifest(video_id: str, transcoded_files: Dict, output_dir: str) -> str:
    """
    Generate DASH manifest (MPD file)

    Returns:
        Path to DASH manifest file
    """
    # Use MP4Box or ffmpeg to generate DASH
    manifest_path = f"{output_dir}/manifest.mpd"

    # Simplified: Use ffmpeg to create DASH
    input_files = [f for r, f in transcoded_files.items() if r.endswith('p')]

    if input_files:
        dash_cmd = [
            'ffmpeg',
            '-i', input_files[0],  # First resolution as base
            '-c', 'copy',
            '-f', 'dash',
            manifest_path
        ]

        subprocess.run(dash_cmd, capture_output=True, check=True)

    logger.info(f"Generated DASH manifest: {manifest_path}")

    return manifest_path


def _get_content_type(file_path: str) -> str:
    """Get MIME type for file"""
    ext = os.path.splitext(file_path)[1].lower()

    content_types = {
        '.mp4': 'video/mp4',
        '.m3u8': 'application/x-mpegURL',
        '.ts': 'video/MP2T',
        '.mpd': 'application/dash+xml',
    }

    return content_types.get(ext, 'application/octet-stream')


def _update_video_status(video_id: str, status: str, output_files: Dict = None, error: str = None):
    """
    Update video status in database

    In production, use database connection from config
    """
    logger.info(f"Updating video {video_id} status to {status}")

    # Pseudo-code for database update
    # import psycopg2
    # conn = psycopg2.connect(DATABASE_URL)
    # cursor = conn.cursor()
    # cursor.execute("UPDATE videos SET transcoding_status = %s WHERE id = %s", (status, video_id))
    # conn.commit()

    pass
