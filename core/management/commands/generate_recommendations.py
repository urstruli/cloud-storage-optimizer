from django.core.management.base import BaseCommand
from core.models import File, Recommendation
from anthropic import Anthropic

class Command(BaseCommand):
    help = 'Generate AI cost optimization recommendations using Claude API'

    def handle(self, *args, **options):
        """
        Analyzes duplicates and stale files, generates recommendations via Claude API.
        """
        
        # Get duplicates and stale files
        duplicates = File.objects.filter(is_duplicate=True)
        stale = File.objects.filter(is_stale=True)
        
        duplicate_count = duplicates.count()
        stale_count = stale.count()
        
        if duplicate_count == 0 and stale_count == 0:
            self.stdout.write(self.style.WARNING('No duplicates or stale files to analyze.'))
            return
        
        # Build analysis summary
        summary = f"""
        Storage Analysis Summary:
        - Duplicate files found: {duplicate_count}
        - Stale files found: {stale_count}
        
        Duplicate files (backup/redundant copies):
        {', '.join([f.file_name for f in duplicates[:5]])}
        
        Stale files (old, archived, temp):
        {', '.join([f.file_name for f in stale[:5]])}
        
        Please provide 3-4 specific, actionable cost optimization recommendations for a VFX/creative team based on these findings.
        """
        
        # Call Claude API
        try:
            client = Anthropic()
            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"Based on this storage analysis, provide cost optimization recommendations:\n{summary}"
                    }
                ]
            )
            
            recommendation_text = message.content[0].text
            
            # Save recommendation to first project
            from core.models import Project
            project = Project.objects.first()
            
            rec = Recommendation.objects.create(
                project=project,
                description=recommendation_text,
                recommendation_type='COST_OPTIMIZATION',
                potential_savings=15,
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ Recommendation generated and saved.\n\n{recommendation_text}'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error calling Claude API: {str(e)}'))