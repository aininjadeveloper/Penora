"""
Integration Examples for External Apps
Shows how other applications can integrate with Penora workspace
"""

import requests
import json
from typing import Dict, List, Any

class ImageGeneIntegration:
    """Example integration for ImageGene to access Penora projects"""
    
    def __init__(self):
        self.penora_base_url = "https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev"
    
    def get_penora_projects_dropdown(self, jwt_token: str, user_id: str) -> List[Dict[str, str]]:
        """Get Penora projects formatted for ImageGene dropdown"""
        try:
            # Authenticate and get projects
            response = requests.get(
                f"{self.penora_base_url}/api/user-projects",
                params={
                    'jwt_token': jwt_token,
                    'user_id': user_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    projects = data.get('projects', [])
                    
                    # Format for dropdown
                    dropdown_options = []
                    for project in projects:
                        title = project.get('title', 'Untitled Project')
                        word_count = project.get('word_count', 0)
                        display_text = f"{title} ({word_count} words)"
                        
                        dropdown_options.append({
                            'value': project.get('id'),
                            'text': display_text,
                            'content': project.get('content', ''),
                            'title': title
                        })
                    
                    return dropdown_options
            
            return []
            
        except Exception as e:
            print(f"Error fetching Penora projects: {e}")
            return []
    
    def use_penora_project_for_prompt(self, project_code: str, jwt_token: str, user_id: str) -> str:
        """Use Penora project content as ImageGene prompt"""
        try:
            response = requests.get(
                f"{self.penora_base_url}/api/project/{project_code}",
                params={
                    'jwt_token': jwt_token,
                    'user_id': user_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    project = data.get('project', {})
                    content = project.get('content', '')
                    
                    # Extract key visual elements for image generation
                    # This could be enhanced with NLP to extract better prompts
                    prompt = self.extract_visual_prompt(content)
                    return prompt
            
            return ""
            
        except Exception as e:
            print(f"Error using Penora project: {e}")
            return ""
    
    def extract_visual_prompt(self, content: str) -> str:
        """Extract visual elements from text content for image generation"""
        # Simple extraction - could be enhanced with AI
        visual_keywords = []
        
        # Look for descriptive words
        descriptive_words = [
            'beautiful', 'dark', 'bright', 'colorful', 'mysterious',
            'ancient', 'modern', 'futuristic', 'peaceful', 'dramatic'
        ]
        
        # Look for objects and settings
        objects = [
            'castle', 'forest', 'mountain', 'ocean', 'city',
            'character', 'hero', 'villain', 'dragon', 'sword'
        ]
        
        content_lower = content.lower()
        
        for word in descriptive_words + objects:
            if word in content_lower:
                visual_keywords.append(word)
        
        # Create prompt from first 100 characters + visual keywords
        base_prompt = content[:100].strip()
        if visual_keywords:
            keyword_string = ", ".join(visual_keywords[:5])
            prompt = f"{base_prompt}, featuring {keyword_string}"
        else:
            prompt = base_prompt
        
        return prompt[:200]  # Limit prompt length

# Example usage for any external app
def integrate_with_penora(app_name: str, jwt_token: str, user_id: str):
    """General integration example"""
    print(f"\n=== {app_name} Integration with Penora ===")
    
    # 1. Get user's projects
    try:
        response = requests.get(
            "https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/api/user-projects",
            params={'jwt_token': jwt_token, 'user_id': user_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                projects = data.get('projects', [])
                print(f"Found {len(projects)} Penora projects")
                
                for project in projects[:3]:  # Show first 3
                    print(f"- {project.get('title')} ({project.get('word_count')} words)")
                
                # 2. Use first project as example
                if projects:
                    project_code = projects[0].get('id')
                    project_response = requests.get(
                        f"https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/api/project/{project_code}",
                        params={'jwt_token': jwt_token, 'user_id': user_id}
                    )
                    
                    if project_response.status_code == 200:
                        project_data = project_response.json()
                        if project_data.get('success'):
                            project = project_data.get('project', {})
                            content = project.get('content', '')
                            print(f"\nProject content preview: {content[:100]}...")
            else:
                print("Failed to get projects")
        else:
            print(f"HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"Integration error: {e}")

# JavaScript/HTML example for frontend integration
FRONTEND_INTEGRATION_EXAMPLE = """
<!-- Example HTML for external app integration -->
<div class="penora-integration">
    <label for="penora-projects">Select Penora Project:</label>
    <select id="penora-projects" onchange="loadPenoraProject()">
        <option value="">Select a Penora project...</option>
    </select>
    <div id="project-content" style="display: none;">
        <h4 id="project-title"></h4>
        <p id="project-preview"></p>
        <button onclick="usePenoraContent()">Use This Content</button>
    </div>
</div>

<script>
// JavaScript for external app integration
async function loadPenoraProjects(jwtToken, userId) {
    try {
        const response = await fetch(`https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/api/user-projects?jwt_token=${jwtToken}&user_id=${userId}`);
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('penora-projects');
            select.innerHTML = '<option value="">Select a Penora project...</option>';
            
            data.projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = `${project.title} (${project.word_count} words)`;
                option.dataset.content = project.content;
                option.dataset.title = project.title;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading Penora projects:', error);
    }
}

function loadPenoraProject() {
    const select = document.getElementById('penora-projects');
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption.value) {
        document.getElementById('project-title').textContent = selectedOption.dataset.title;
        document.getElementById('project-preview').textContent = selectedOption.dataset.content.substring(0, 200) + '...';
        document.getElementById('project-content').style.display = 'block';
    } else {
        document.getElementById('project-content').style.display = 'none';
    }
}

function usePenoraContent() {
    const select = document.getElementById('penora-projects');
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption.value) {
        const content = selectedOption.dataset.content;
        const title = selectedOption.dataset.title;
        
        // Use the content in your external app
        // For ImageGene: populate prompt field
        // For other apps: use as needed
        document.getElementById('your-app-input-field').value = content;
        
        alert(`Loaded Penora project: ${title}`);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Get JWT token and user ID from your app's authentication
    const jwtToken = 'your-jwt-token';
    const userId = 'your-user-id';
    
    loadPenoraProjects(jwtToken, userId);
});
</script>
"""

if __name__ == "__main__":
    # Example usage
    print("Penora Cross-App Integration Examples")
    print("=" * 40)
    
    # Example for ImageGene
    imagegene = ImageGeneIntegration()
    print("ImageGene integration class created")
    
    # Example for any external app
    print("\nFor integration with any external app:")
    print("1. Use the API endpoints:")
    print("   - GET /api/user-projects")
    print("   - GET /api/project/<project_code>")
    print("   - POST /api/cross-app/auth")
    print("\n2. Include JWT token and user_id in requests")
    print("\n3. See integration_examples.py for complete code examples")