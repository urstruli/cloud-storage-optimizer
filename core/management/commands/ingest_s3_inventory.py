from django.core.management.base import BaseCommand
from core.models import File, Project
from datetime import datetime
import random

class Command(BaseCommand):
    help = 'Ingest mock S3 Inventory data and populate File records'

    def handle(self, *args, **options):
        """
        Simulates S3 Inventory CSV ingestion.
        Creates mock file records for demo purposes.
        """
        
        # Mock S3 file data (simulates CSV from S3 Inventory)
        mock_files = [
            {'name': 'hero_shot_v1.exr', 'size': 5000000000, 'project_id': 1},
            {'name': 'hero_shot_v2.exr', 'size': 5200000000, 'project_id': 1},
            {'name': 'hero_shot_v1_backup.exr', 'size': 5000000000, 'project_id': 1},  # Duplicate
            {'name': 'character_rig_v3.mb', 'size': 800000000, 'project_id': 1},
            {'name': 'environment_v5.ma', 'size': 2000000000, 'project_id': 1},
            {'name': 'textures_diffuse_4k.zip', 'size': 3000000000, 'project_id': 1},
            {'name': 'music_track_final.wav', 'size': 600000000, 'project_id': 2},
            {'name': 'music_track_final_backup.wav', 'size': 600000000, 'project_id': 2},  # Duplicate
            {'name': 'voiceover_takes.zip', 'size': 1500000000, 'project_id': 2},
            {'name': 'temp_old_archive_2024.tar', 'size': 8000000000, 'project_id': 2},  # Stale
        ]
        
        # Clear existing files (optional - comment out if you want to keep old data)
        # File.objects.all().delete()
        
        created_count = 0
        for file_data in mock_files:
            file, created = File.objects.get_or_create(
                file_name=file_data['name'],
                project_id=file_data['project_id'],
                defaults={
                    'file_size': file_data['size'],
                    's3_key': f"s3://bucket/{file_data['project_id']}/{file_data['name']}",
                    'storage_class': 'STANDARD',
                    'is_duplicate': False,
                    'is_stale': False,
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ S3 Inventory ingestion complete. {created_count} new files created.'
            )
        )