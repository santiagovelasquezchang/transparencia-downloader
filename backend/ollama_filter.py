import ollama
import sqlite3
import hashlib
import json
import pandas as pd
import os

class OllamaContactFilter:
    def __init__(self, cache_file="filter_cache.db"):
        self.client = ollama.Client()
        self.cache_file = cache_file
        self._init_cache()
        
        # Target categories (Spanish keywords for better matching)
        self.target_categories = [
            "tecnología", "sistemas", "informática", "digital",
            "administración", "administrativo", "gestión",
            "planeación", "proyectos", "planificación", 
            "innovación", "desarrollo", "modernización",
            "digitalización", "transformación digital",
            "compras", "adquisiciones", "contrataciones"
        ]
    
    def _init_cache(self):
        """Initialize SQLite cache for job title classifications"""
        conn = sqlite3.connect(self.cache_file)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS filter_cache (
                title_hash TEXT PRIMARY KEY,
                is_relevant INTEGER,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def _get_cache_key(self, job_title):
        """Generate consistent hash for job title"""
        return hashlib.md5(job_title.lower().strip().encode()).hexdigest()
    
    def _check_cache(self, job_title):
        """Check if job title was already classified"""
        cache_key = self._get_cache_key(job_title)
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.execute(
            "SELECT is_relevant, category FROM filter_cache WHERE title_hash = ?", 
            (cache_key,)
        )
        result = cursor.fetchone()
        conn.close()
        return result  # (is_relevant, category) or None
    
    def _save_to_cache(self, job_title, is_relevant, category):
        """Save classification to cache"""
        cache_key = self._get_cache_key(job_title)
        conn = sqlite3.connect(self.cache_file)
        conn.execute(
            "INSERT OR REPLACE INTO filter_cache (title_hash, is_relevant, category) VALUES (?, ?, ?)",
            (cache_key, int(is_relevant), category)
        )
        conn.commit()
        conn.close()
    
    def filter_contacts_batch(self, contacts_df):
        """Main filtering method with batch processing and caching"""
        if contacts_df.empty:
            return contacts_df
        
        # Get unique job titles
        job_title_column = self._find_job_title_column(contacts_df)
        if not job_title_column:
            print("⚠️  No job title column found")
            return contacts_df
        
        unique_titles = contacts_df[job_title_column].dropna().unique()
        print(f"🔍 Processing {len(unique_titles)} unique job titles...")
        
        # Check cache first
        cached_results = {}
        uncached_titles = []
        
        for title in unique_titles:
            if pd.isna(title) or str(title).strip() == '':
                continue
            cached = self._check_cache(str(title))
            if cached:
                cached_results[str(title)] = {'is_relevant': bool(cached[0]), 'category': cached[1]}
            else:
                uncached_titles.append(str(title))
        
        print(f"💾 Found {len(cached_results)} cached results")
        print(f"🤖 Need to process {len(uncached_titles)} new titles with Ollama")
        
        # Process uncached titles with Ollama (batch)
        if uncached_titles:
            ollama_results = self._classify_with_ollama(uncached_titles)
            
            # Save to cache and merge results
            for title, result in ollama_results.items():
                self._save_to_cache(title, result['is_relevant'], result['category'])
                cached_results[title] = result
        
        # Filter the dataframe
        relevant_titles = {title for title, result in cached_results.items() if result['is_relevant']}
        filtered_df = contacts_df[contacts_df[job_title_column].astype(str).isin(relevant_titles)]
        
        print(f"✅ Filtered: {len(contacts_df)} → {len(filtered_df)} contacts ({len(filtered_df)/len(contacts_df)*100:.1f}%)")
        return filtered_df
    
    def _find_job_title_column(self, df):
        """Find the job title column in the dataframe"""
        possible_columns = ['Denominación del cargo', 'Cargo', 'Puesto', 'denominacion', 'cargo']
        for col in df.columns:
            if any(possible in col for possible in possible_columns):
                return col
        return None
    
    def _classify_with_ollama(self, job_titles):
        """Classify job titles using Ollama in batch"""
        # Create numbered list for batch processing
        titles_text = '\n'.join([f"{i+1}. {title}" for i, title in enumerate(job_titles)])
        
        prompt = f"""
Analiza estos puestos del gobierno mexicano. Mantén SOLO los relacionados con:
- Tecnología/Sistemas/Informática
- Administración/Gestión
- Planeación/Proyectos  
- Innovación/Desarrollo
- Digitalización
- Compras/Adquisiciones

Puestos:
{titles_text}

Responde SOLO con los números de puestos relevantes (separados por comas):
Ejemplo: 1,3,7,12
"""
        
        try:
            response = self.client.chat(
                model='llama3.2:1b',
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0}  # Consistent results
            )
            
            # Parse response
            relevant_numbers = []
            response_text = response['message']['content'].strip()
            
            print(f"🤖 Ollama response: {response_text}")
            
            if response_text and response_text.lower() not in ["ninguno", "none", "0"]:
                try:
                    # Handle various response formats
                    clean_response = response_text.replace(" ", "").replace("\n", "")
                    if clean_response.isdigit():
                        relevant_numbers = [int(clean_response) - 1]
                    else:
                        relevant_numbers = [int(x.strip()) - 1 for x in clean_response.split(',') if x.strip().isdigit()]
                except Exception as parse_error:
                    print(f"⚠️  Could not parse Ollama response: {response_text} - Error: {parse_error}")
            
            # Build results dictionary
            results = {}
            for i, title in enumerate(job_titles):
                is_relevant = i in relevant_numbers
                category = "tech-related" if is_relevant else "not-relevant"
                results[title] = {'is_relevant': is_relevant, 'category': category}
            
            print(f"✅ Classified {len([r for r in results.values() if r['is_relevant']])} as relevant out of {len(job_titles)}")
            return results
            
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            print("⚠️  Ollama might not be running. Install with: curl -fsSL https://ollama.ai/install.sh | sh")
            print("⚠️  Then run: ollama pull llama3.2:1b")
            # Fallback: return all as not relevant
            return {title: {'is_relevant': False, 'category': 'error'} for title in job_titles}

    def test_ollama_connection(self):
        """Test if Ollama is working"""
        try:
            response = self.client.chat(
                model='llama3.2:1b',
                messages=[{'role': 'user', 'content': 'Hello, respond with just "OK"'}],
                options={'temperature': 0}
            )
            return True, response['message']['content']
        except Exception as e:
            return False, str(e)
