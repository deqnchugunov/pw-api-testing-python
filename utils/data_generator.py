from faker import Faker
import random
from typing import Dict, List, Any
from datetime import datetime
import json


class DataGenerator:
    """Data generator for test data"""
    
    def __init__(self):
        self.fake = Faker()
        Faker.seed(42)  # For reproducible results
    
    def get_new_random_article(self) -> Dict[str, Any]:
        """
        Get new random article
        
        Returns:
            Dictionary with article data
        """
        title = self.fake.sentence()
        slug_id = self._generate_slug_id()
        
        return {
            "article": {
                "title": f"{title} [{slug_id}]",
                "description": self.fake.paragraph(),
                "body": self.fake.paragraphs(nb=3),
                "tagList": [
                    self.fake.word(),
                    "Test",
                    self.fake.word()
                ]
            }
        }
    
    def get_new_random_user(self) -> Dict[str, Any]:
        """
        Get new random user
        
        Returns:
            Dictionary with user data
        """
        username = self.fake.user_name().lower().replace('.', '_')
        
        return {
            "user": {
                "email": self.fake.email().lower(),
                "password": self.fake.password(length=12),
                "username": username
            }
        }
    
    def _generate_slug_id(self) -> str:
        """Generate slug ID in pattern from screenshot"""
        if random.random() > 0.5:
            # Pattern: 123.AB.2024
            num = random.randint(1, 999)
            letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
            year = random.randint(2020, 2024)
            return f"{num}.{letters}.{year}"
        else:
            # Pattern: 2024.01.2024
            year = random.randint(2020, 2024)
            month = str(random.randint(1, 12)).zfill(2)
            id_num = random.randint(1000, 9999)
            return f"{year}.{month}.{id_num}"
    
    def extract_slug_id(self, title: str) -> str:
        """
        Extract slug ID from title
        
        Args:
            title: Article title
            
        Returns:
            Slug ID
        """
        import re
        match = re.search(r'\[(.*?)\]', title)
        return match.group(1) if match else ''
    
    def get_random_tags(self, count: int = 5) -> List[str]:
        """
        Generate random tags
        
        Args:
            count: Number of tags to generate
            
        Returns:
            List of tags
        """
        return [self.fake.word() for _ in range(count)]
    
    def get_random_comment(self) -> str:
        """Generate random comment"""
        return self.fake.paragraph()
    
    def get_random_article_payload(self) -> str:
        """Generate random article payload as JSON string"""
        article = self.get_new_random_article()
        return json.dumps(article)
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()


# Singleton instance
data_generator = DataGenerator()

# Convenience function as shown in screenshot
def get_new_random_article() -> Dict[str, Any]:
    """Get new random article (function interface)"""
    return data_generator.get_new_random_article()