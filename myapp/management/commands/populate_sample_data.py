from django.core.management.base import BaseCommand
from myapp.models import DebateCategory, DebateTopic

class Command(BaseCommand):
    help = 'Populate database with sample debate categories and topics'
    
    def handle(self, *args, **options):
        #categories
        categories_data = [
            {
                'name': 'Technology',
                'description': 'Debates about technology, AI, social media, and digital innovation',
                'topics': [
                    {'title': 'AI will replace most human jobs', 'difficulty': 'medium'},
                    {'title': 'Social media does more harm than good', 'difficulty': 'easy'},
                    {'title': 'Privacy is dead in the digital age', 'difficulty': 'hard'},
                    {'title': 'Smartphones should be banned in schools', 'difficulty': 'easy'},
                    {'title': 'Cryptocurrency is the future of money', 'difficulty': 'medium'},
                ]
            },
            {
                'name': 'Education',
                'description': 'Debates about learning, schools, and educational systems',
                'topics': [
                    {'title': 'Online learning is better than traditional classroom learning', 'difficulty': 'easy'},
                    {'title': 'College education is overrated', 'difficulty': 'medium'},
                    {'title': 'Standardized testing should be abolished', 'difficulty': 'medium'},
                    {'title': 'Students should choose their own curriculum', 'difficulty': 'hard'},
                    {'title': 'Homework is unnecessary for learning', 'difficulty': 'easy'},
                ]
            },
            {
                'name': 'Environment',
                'description': 'Debates about climate change, sustainability, and environmental issues',
                'topics': [
                    {'title': 'Climate change is the most urgent global issue', 'difficulty': 'medium'},
                    {'title': 'Nuclear energy is the solution to climate change', 'difficulty': 'hard'},
                    {'title': 'Individuals are more responsible than corporations for environmental damage', 'difficulty': 'medium'},
                    {'title': 'Electric cars will solve transportation pollution', 'difficulty': 'easy'},
                    {'title': 'Veganism is necessary to save the environment', 'difficulty': 'hard'},
                ]
            },
            {
                'name': 'Society',
                'description': 'Debates about social issues, culture, and human behavior',
                'topics': [
                    {'title': 'Money can buy happiness', 'difficulty': 'easy'},
                    {'title': 'Social media influencers have too much power', 'difficulty': 'medium'},
                    {'title': 'Working from home is better than office work', 'difficulty': 'easy'},
                    {'title': 'Universal basic income should be implemented', 'difficulty': 'hard'},
                    {'title': 'Competitive sports are harmful to young people', 'difficulty': 'medium'},
                ]
            },
            {
                'name': 'Politics',
                'description': 'Debates about government, democracy, and political systems',
                'topics': [
                    {'title': 'Democracy is the best form of government', 'difficulty': 'hard'},
                    {'title': 'Voting should be mandatory', 'difficulty': 'medium'},
                    {'title': 'Politicians should have term limits', 'difficulty': 'medium'},
                    {'title': 'Social media should be regulated by government', 'difficulty': 'hard'},
                    {'title': 'Taxes on the wealthy should be increased', 'difficulty': 'medium'},
                ]
            },
            {
                'name': 'Health',
                'description': 'Debates about healthcare, fitness, and wellness',
                'topics': [
                    {'title': 'Healthcare should be free for everyone', 'difficulty': 'medium'},
                    {'title': 'Fast food companies are responsible for obesity', 'difficulty': 'easy'},
                    {'title': 'Mental health is as important as physical health', 'difficulty': 'easy'},
                    {'title': 'Alternative medicine is as effective as conventional medicine', 'difficulty': 'hard'},
                    {'title': 'Sugar should be taxed like tobacco', 'difficulty': 'medium'},
                ]
            }
        ]
        
        self.stdout.write('Creating categories and topics...')
        
        for category_data in categories_data:
            category, created = DebateCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            
            if created:
                self.stdout.write(f'Created category: {category.name}')
            
            #topics
            for topic_data in category_data['topics']:
                topic, created = DebateTopic.objects.get_or_create(
                    category=category,
                    title=topic_data['title'],
                    defaults={
                        'description': f"Debate topic: {topic_data['title']}",
                        'difficulty_level': topic_data['difficulty']
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created topic: {topic.title} ({topic.difficulty_level})')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data!')
        )