from django.core.management.base import BaseCommand
from core.models import File
from datetime import datetime, timedelta
from hashlib import md5

class Command(BaseCommand):
    help = 'Analyze files for duplicates and stale data'

    def handle(self, *args, **options):
        """
        Analyzes all files in the system:
        1. Detects duplicates (same size, likely same file)
        2. Flags stale files (not modified in 90+ days, archive/temp names)
        """
        
        # Reset flags
        File.objects.all().update(is_duplicate=False, is_stale=False)
        
        # === DUPLICATE DETECTION ===
        # Files with same size are potential duplicates
        from django.db.models import Count
        duplicate_sizes = (
            File.objects
            .values('file_size')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        
        duplicates_found = 0
        for dup in duplicate_sizes:
            files_with_size = File.objects.filter(file_size=dup['file_size'])
            # Mark all but the first as duplicate
            for file in files_with_size[1:]:
                file.is_duplicate = True
                file.save()
                duplicates_found += 1
        
        # === STALE FILE DETECTION ===
        # Files older than 90 days OR with temp/archive names
        stale_threshold = datetime.now() - timedelta(days=90)
        stale_patterns = ['temp', 'old', 'archive', 'backup', 'bak', '_v1', '_v2']
        
        stale_files = File.objects.filter(created_at__lt=stale_threshold)
        stale_count = 0
        
        for file in stale_files:
            file.is_stale = True
            file.save()
            stale_count += 1
        
        # Also flag files matching stale patterns by name
        for pattern in stale_patterns:
            pattern_files = File.objects.filter(file_name__icontains=pattern, is_stale=False)
            for file in pattern_files:
                file.is_stale = True
                file.save()
                stale_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Analysis complete.\n'
                f'  - {duplicates_found} duplicate files detected\n'
                f'  - {stale_count} stale files flagged'
            )
        )