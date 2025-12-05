import os
import logging
from deepinfra_client import ask_deepinfra, get_model_config, DEEPINFRA_MODELS

class AIService:
    def __init__(self):
        # Check if DeepInfra API key is available
        self.available = bool(os.environ.get("DEEPINFRA_API_KEY"))
        if not self.available:
            logging.error("DEEPINFRA_API_KEY not found in environment variables")
        
        # Use the corrected model configurations from deepinfra_client_fixed
        self.models = DEEPINFRA_MODELS
    
    def generate_text(self, prompt, model_type='balanced', length='medium'):
        """Generate text with model selection and length control"""
        if not self.available:
            return {
                "success": False,
                "error": "AI service is temporarily unavailable. Please try again in a moment."
            }
            
        try:
            model_config = self.models.get(model_type, self.models['balanced'])
            
            # Length-based prompts
            length_prompts = {
                'short': f"Write a short paragraph (100-150 words) about: {prompt}",
                'medium': f"Write a full page (300-500 words) about: {prompt}",
                'long': f"Write a full chapter (500+ words) about: {prompt}. Include detailed descriptions, dialogue, and character development."
            }
            
            enhanced_prompt = length_prompts.get(length, length_prompts['medium'])
            system_msg = f"You are a skilled {model_config['display_name'].lower()} writing assistant. Generate high-quality, engaging content."
            
            content = ask_deepinfra(
                enhanced_prompt, 
                system_msg, 
                model_config['name'],
                model_config['max_tokens']
            )
            
            return {
                "success": True,
                "content": content,
                "model_used": model_config['display_name'],
                "length": length,
                "word_count": len(content.split()) if content else 0
            }
                
        except Exception as e:
            logging.error(f"AI service exception: {str(e)}")
            return {
                "success": False,
                "error": "AI service is temporarily unavailable. Please try again in a moment."
            }
    
    def generate_story_chapter(self, story_context, chapter_number, total_chapters, model_type='creative', max_tokens=2500):
        """Generate a single chapter of a story using DeepInfra with model selection"""
        if not self.available:
            return {
                "success": False,
                "error": "AI service is temporarily unavailable. Please try again in a moment."
            }
            
        try:
            model_config = self.models.get(model_type, self.models['creative'])
            
            prompt = f"""
            Story Context: {story_context}
            
            Write Chapter {chapter_number} of {total_chapters} for this story. 
            Make it engaging, well-structured, and write around 500-600 words (one printed page) for this chapter while keeping the existing narrative style.
            Ensure it flows naturally from the previous chapters and advances the plot.
            Include multiple paragraphs with detailed descriptions, dialogue, and character development.
            """
            
            system_msg = "You are a skilled storyteller. Write engaging, well-structured chapters that advance the narrative."
            content = ask_deepinfra(
                prompt, 
                system_msg, 
                model_config['name'],
                min(max_tokens, model_config['max_tokens'])
            )
            
            return {
                "success": True,
                "content": content,
                "model_used": model_config['display_name'],
                "chapter_number": chapter_number,
                "word_count": len(content.split()) if content else 0
            }
            
        except Exception as e:
            logging.error(f"Story chapter generation exception: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate chapter: {str(e)}"
            }
    
    def process_uploaded_file(self, file_content, instruction, model_type='balanced'):
        """Process uploaded file with user instruction"""
        if not self.available:
            return {
                "success": False,
                "error": "AI service is temporarily unavailable. Please try again in a moment."
            }
            
        try:
            model_config = self.models.get(model_type, self.models['balanced'])
            
            # Limit file content to prevent token overflow
            max_content_length = 3000
            if len(file_content) > max_content_length:
                file_content = file_content[:max_content_length] + "..."
            
            prompt = f"""
            Based on this existing content:
            
            {file_content}
            
            User instruction: {instruction}
            
            Please {instruction.lower()} the content while maintaining quality and coherence.
            """
            
            system_msg = f"You are a professional editor and writer. Help improve and transform content based on user requests."
            
            content = ask_deepinfra(
                prompt,
                system_msg,
                model_config['name'],
                model_config['max_tokens']
            )
            
            return {
                "success": True,
                "content": content,
                "model_used": model_config['display_name'],
                "instruction": instruction,
                "word_count": len(content.split()) if content else 0
            }
            
        except Exception as e:
            logging.error(f"File processing exception: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to process file: {str(e)}"
            }

    def get_model_options(self):
        """Get available model options for UI dropdown"""
        return {key: {
            'display_name': config['display_name'],
            'description': config['description'],
            'cost_multiplier': config['cost_multiplier']
        } for key, config in self.models.items()}

    def generate_story_with_model(self, story_prompt, page_count, model_type='creative'):
        """Generate multi-page story with model selection"""
        if not self.available:
            return None
            
        try:
            model_config = self.models.get(model_type, self.models['creative'])
            story_parts = []
            
            for i in range(page_count):
                chapter_prompt = f"""
                Story: {story_prompt}
                
                Write page {i+1} of {page_count} for this story.
                Each page should be around 300-500 words.
                Make it engaging and well-structured.
                """
                
                system_msg = f"You are a skilled storyteller using {model_config['display_name']} style. Create engaging content."
                
                content = ask_deepinfra(
                    chapter_prompt,
                    system_msg,
                    model=model_config['name'],
                    max_tokens=model_config['max_tokens']
                )
                
                if content:
                    story_parts.append(f"=== PAGE {i+1} ===\n\n{content}")
                else:
                    return None
            
            return "\n\n".join(story_parts)
            
        except Exception as e:
            logging.error(f"Story generation with model exception: {str(e)}")
            return None

    def generate_story_title(self, story_prompt):
        """Generate a title for a story using DeepInfra"""
        if not self.available:
            return {
                "success": False,
                "title": "Generated Story"
            }
        
        try:
            prompt = f"Generate a compelling, creative title for a story about: {story_prompt}. Return only the title, no quotes or extra text."
            system_msg = "You are a title generator. Create short, catchy titles for stories."
            title = ask_deepinfra(prompt, system_msg, "mistralai/Mixtral-8x7B-Instruct-v0.1", 50)
            
            return {
                "success": True,
                "title": title.strip()
            }
            
        except Exception as e:
            logging.error(f"Title generation exception: {str(e)}")
            return {
                "success": False,
                "title": "Generated Story"
            }

    def generate_single_text(self, prompt):
        """Generate single text from prompt"""
        if not self.available:
            return None
            
        try:
            system_msg = "You are a creative writing assistant. Generate high-quality, engaging content based on the user's prompt. Write approximately 800-1200 words with proper structure and flow."
            content = ask_deepinfra(prompt, system_msg, "mistralai/Mixtral-8x7B-Instruct-v0.1", 2000)
            return content
            
        except Exception as e:
            logging.error(f"Error in AI text generation: {e}")
            return None

    def generate_story(self, prompt, page_count):
        """Generate multi-page story from prompt"""
        if not self.available:
            return None
            
        try:
            # Optimize for different page counts with improved limits for large pages
            if page_count <= 5:
                words_per_page = 800
                max_tokens = page_count * 1200
            elif page_count <= 20:
                words_per_page = 600
                max_tokens = page_count * 900
            elif page_count <= 50:
                words_per_page = 400
                max_tokens = min(page_count * 600, 6000)
            else:
                # For very large page counts (50+), generate an outline approach
                words_per_page = 200
                max_tokens = min(3000, page_count * 50)  # Very conservative for 100+ pages
            
            # For large page counts, use a different approach
            if page_count > 50:
                story_prompt = f"Create a detailed {page_count}-page story outline and first few pages about: {prompt}. Structure it as: Title, Plot Summary, Character Overview, then write the first 3-5 pages in detail with 'Page X:' headers. For the remaining pages, provide chapter summaries."
                system_msg = f"You are a professional storyteller. Create a comprehensive story structure for {page_count} pages with detailed opening and summaries for the rest."
            else:
                story_prompt = f"Create a {page_count}-page story about: {prompt}. Structure it with clear page breaks. Each page should be approximately {words_per_page} words. Use 'Page X:' headers to separate pages clearly."
                system_msg = f"You are a professional storyteller. Create a {page_count}-page story with engaging narrative, character development, and proper structure. Keep each page concise but engaging with approximately {words_per_page} words per page."
            
            content = ask_deepinfra(story_prompt, system_msg, "mistralai/Mixtral-8x7B-Instruct-v0.1", max_tokens)
            return content
            
        except Exception as e:
            logging.error(f"Error in AI story generation: {e}")
            return None

    def format_story_display(self, story_content):
        """Format story content for better display"""
        if not story_content:
            return story_content
        
        # Add some basic formatting for better readability
        formatted = story_content.replace('\n\n', '\n\n')
        
        # Ensure proper spacing around page headers
        if 'Page ' in formatted:
            formatted = formatted.replace('Page ', '\n\nPage ')
        
        return formatted.strip()
    
    def process_uploaded_file(self, file_content, instruction, model_type='balanced'):
        """Process uploaded file content with AI enhancement"""
        if not self.available:
            return {
                "success": False,
                "error": "AI service not available"
            }
            
        try:
            model_config = self.models.get(model_type, self.models['balanced'])
            
            # Create processing prompt based on instruction
            instruction_prompts = {
                'expand': 'Expand and add more details and content to this text while maintaining its core message and style:',
                'fine-tune': 'Improve the writing quality, style, and readability of this text without changing its core content:',
                'convert to script': 'Convert this narrative into a screenplay format with proper dialogue and scene directions:',
                'summarize': 'Create a concise summary of this text while capturing all key points:',
                'continue': 'Continue this story from where it ends, maintaining the same style and tone:'
            }
            
            prompt_prefix = instruction_prompts.get(instruction, f"Please {instruction} this text:")
            enhanced_prompt = f"{prompt_prefix}\n\n{file_content}"
            
            system_msg = f"You are a skilled editor using {model_config['display_name']} style. Follow the instructions precisely while maintaining quality."
            
            result = ask_deepinfra(
                enhanced_prompt,
                system_msg,
                model=model_config['name'],
                max_tokens=model_config['max_tokens']
            )
            
            if result:
                return {
                    "success": True,
                    "content": result,
                    "model_used": model_type,
                    "word_count": len(result.split()) if result else 0
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to process file content"
                }
                
        except Exception as e:
            logging.error(f"File processing exception: {str(e)}")
            return {
                "success": False,
                "error": f"Processing error: {str(e)}"
            }

    def sudowrite_write_tool(self, prompt, mode='auto', variants=1, temperature=0.7, model_type='balanced'):
        """Sudowrite-like Write tool with multiple modes and variants"""
        if not self.available:
            return {"success": False, "error": "AI service unavailable"}
            
        try:
            model_config = self.models.get(model_type, self.models['balanced'])
            results = []
            
            mode_prompts = {
                'auto': f"Continue this story naturally: {prompt}",
                'guided': f"Continue this story following the user's direction: {prompt}",
                'tone_shift_ominous': f"Continue this story with an ominous, foreboding tone: {prompt}",
                'tone_shift_romantic': f"Continue this story with a romantic, tender tone: {prompt}",
                'tone_shift_mysterious': f"Continue this story with a mysterious, suspenseful tone: {prompt}"
            }
            
            system_msg = f"You are a creative writing assistant. Generate high-quality content with temperature {temperature}."
            
            for i in range(variants):
                content = ask_deepinfra(
                    mode_prompts.get(mode, mode_prompts['auto']),
                    system_msg,
                    model=model_config['name'],
                    max_tokens=model_config['max_tokens']
                )
                
                if content:
                    results.append({
                        'variant': i + 1,
                        'content': content,
                        'word_count': len(content.split())
                    })
            
            return {
                "success": True,
                "variants": results,
                "mode": mode,
                "model_used": model_config['display_name']
            }
            
        except Exception as e:
            logging.error(f"Write tool error: {str(e)}")
            return {"success": False, "error": f"Generation error: {str(e)}"}

    def sudowrite_rewrite_tool(self, text, rewrite_type='improve', model_type='balanced'):
        """Sudowrite-like Rewrite tool for passage improvements"""
        if not self.available:
            return {"success": False, "error": "AI service unavailable"}
            
        try:
            model_config = self.models.get(model_type, self.models['balanced'])
            
            rewrite_prompts = {
                'show_not_tell': f"Rewrite this passage using 'show don't tell' techniques - replace exposition with action, dialogue, and sensory details:\n\n{text}",
                'tone_change': f"Rewrite this passage with a different tone while keeping the same events:\n\n{text}",
                'expand': f"Expand this passage with more detail, description, and development:\n\n{text}",
                'shorten': f"Condense this passage while keeping the key information and impact:\n\n{text}",
                'improve': f"Improve the writing quality, flow, and readability of this passage:\n\n{text}"
            }
            
            prompt = rewrite_prompts.get(rewrite_type, rewrite_prompts['improve'])
            system_msg = "You are an expert editor. Rewrite the given text according to the specific instructions while maintaining the author's voice."
            
            content = ask_deepinfra(
                prompt,
                system_msg,
                model=model_config['name'],
                max_tokens=model_config['max_tokens']
            )
            
            return {
                "success": True,
                "original": text,
                "rewritten": content,
                "type": rewrite_type,
                "model_used": model_config['display_name']
            }
            
        except Exception as e:
            logging.error(f"Rewrite tool error: {str(e)}")
            return {"success": False, "error": f"Rewrite error: {str(e)}"}

    def sudowrite_describe_tool(self, text, sense_focus='all', model_type='balanced'):
        """Sudowrite-like Describe tool for sensory details"""
        if not self.available:
            return {"success": False, "error": "AI service unavailable"}
            
        try:
            model_config = self.models.get(model_type, self.models['balanced'])
            
            sense_prompts = {
                'sight': f"Add rich visual descriptions to this passage - colors, shapes, lighting, movement:\n\n{text}",
                'sound': f"Add detailed sound descriptions to this passage - noises, music, voices, ambient sounds:\n\n{text}",
                'smell': f"Add detailed smell and scent descriptions to this passage:\n\n{text}",
                'taste': f"Add taste descriptions where appropriate to this passage:\n\n{text}",
                'touch': f"Add tactile and texture descriptions to this passage:\n\n{text}",
                'metaphor': f"Add metaphors and figurative language to enrich this passage:\n\n{text}",
                'all': f"Add rich sensory details (sight, sound, smell, taste, touch) and metaphors to bring this passage to life:\n\n{text}"
            }
            
            prompt = sense_prompts.get(sense_focus, sense_prompts['all'])
            system_msg = "You are a master of descriptive writing. Enhance the given text with vivid, specific sensory details."
            
            content = ask_deepinfra(
                prompt,
                system_msg,
                model=model_config['name'],
                max_tokens=model_config['max_tokens']
            )
            
            return {
                "success": True,
                "original": text,
                "enhanced": content,
                "sense_focus": sense_focus,
                "model_used": model_config['display_name']
            }
            
        except Exception as e:
            logging.error(f"Describe tool error: {str(e)}")
            return {"success": False, "error": f"Description error: {str(e)}"}

    def sudowrite_brainstorm_tool(self, category, context="", count=10, model_type='fast'):
        """Sudowrite-like Brainstorm tool for generating lists"""
        if not self.available:
            return {"success": False, "error": "AI service unavailable"}
            
        try:
            model_config = self.models.get(model_type, self.models['fast'])  # Use fast model for brainstorming
            
            category_prompts = {
                'names': f"Generate {count} unique character names for this context: {context}",
                'plot_ideas': f"Generate {count} creative plot ideas for this context: {context}",
                'objects': f"Generate {count} interesting objects/items for this context: {context}",
                'locations': f"Generate {count} unique locations/settings for this context: {context}",
                'conflicts': f"Generate {count} potential conflicts or tensions for this context: {context}",
                'dialogue': f"Generate {count} interesting dialogue snippets for this context: {context}",
                'world_building': f"Generate {count} world-building elements (customs, rules, features) for this context: {context}"
            }
            
            prompt = category_prompts.get(category, f"Generate {count} creative ideas for {category} in this context: {context}")
            system_msg = f"You are a creative brainstorming assistant. Generate exactly {count} diverse, specific, and interesting suggestions. Format as a numbered list."
            
            content = ask_deepinfra(
                prompt,
                system_msg,
                model=model_config['name'],
                max_tokens=1000
            )
            
            return {
                "success": True,
                "category": category,
                "context": context,
                "suggestions": content,
                "count": count,
                "model_used": model_config['display_name']
            }
            
        except Exception as e:
            logging.error(f"Brainstorm tool error: {str(e)}")
            return {"success": False, "error": f"Brainstorm error: {str(e)}"}

# Create a global instance
ai_service = AIService()

def generate_text_simple(prompt, model_type='balanced', pages=1):
    """
    Simplified generation function that handles both single and multi-page requests.
    This acts as a bridge between the route handlers and the AIService class.
    """
    try:
        if pages > 1:
            # Multi-page generation
            # Use generate_story_with_model for better control
            content = ai_service.generate_story_with_model(prompt, pages, model_type)
            if content:
                return {
                    "success": True, 
                    "content": content, 
                    "model_used": model_type
                }
            else:
                return {
                    "success": False, 
                    "error": "Failed to generate content"
                }
        else:
            # Single page generation
            # Map request to generate_text
            return ai_service.generate_text(prompt, model_type, length='long')
            
    except Exception as e:
        logging.error(f"generate_text_simple error: {e}")
        return {
            "success": False, 
            "error": str(e)
        }