#!/usr/bin/env python3
"""
IntelliRadar Intelligence Analyzer
Core intelligence analysis module for threat intelligence extraction and analysis
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add Intelliradar to path for imports
intelliradar_path = Path(__file__).parent
sys.path.insert(0, str(intelliradar_path))

from utils.llmquery import LLMAgent

class IntelligenceAnalyzer:
    """IntelliRadar Intelligence Analyzer - Core threat intelligence analysis engine"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Setup paths
        self.intelliradar_dir = Path(__file__).parent.parent
        
        # Initialize LLM agent
        self.llm_agent = LLMAgent()
        
        # Load prompts and entity definitions
        self._load_prompts()
        self._load_entity_definitions()
        
        # Load common words for filtering
        self.common_words_file = self.intelliradar_dir / "archive" / "words.txt"
        self.common_words = self._load_common_words()
    
    def _load_prompts(self) -> None:
        """Load analysis prompts from files"""
        prompts_dir = self.intelliradar_dir / "prompts" / "LtM_prompts"
        
        self.prompts = {}
        prompt_files = {
            'extract': 'entityextract_cot_fewshot',
            'relation': 'entityrelation_cot_fewshot', 
            'verify': 'infoverify_cot_fewshot'
        }
        
        for key, filename in prompt_files.items():
            file_path = prompts_dir / filename
            with open(file_path, 'r', encoding='utf-8') as f:
                self.prompts[key] = f.read().strip()
    
    def _load_entity_definitions(self) -> None:
        """Load entity definitions"""
        entity_file = self.intelliradar_dir / "prompts" / "EntityRules" / "entity-1"
        with open(entity_file, 'r', encoding='utf-8') as f:
            self.entity_definitions = f.read().strip()
    
    def _load_common_words(self) -> set:
        """Load common words for filtering"""
        if self.common_words_file.exists():
            with open(self.common_words_file, 'r', encoding='utf-8') as f:
                return set(word.strip().lower() for word in f.readlines() if word.strip())
        return set()
    
    def _extract_threat_indicators(self, content: str) -> List[str]:
        """Extract potential threat indicators (packages, domains, IPs, etc.) using regex patterns"""
        patterns = [
            r'\b[a-zA-Z][a-zA-Z0-9_.-]*[a-zA-Z0-9]\b',
            r'\b[a-zA-Z][a-zA-Z0-9_-]*\b',
            r'["\'][a-zA-Z][a-zA-Z0-9_.-]*[a-zA-Z0-9]["\']',
        ]
        
        threat_indicators = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                clean_match = match.strip('\'"')
                
                if (len(clean_match) >= 2 and 
                    clean_match.lower() not in self.common_words and
                    not clean_match.isdigit() and
                    not re.match(r'^[0-9.-]+$', clean_match)):
                    threat_indicators.add(clean_match)
        
        return sorted(list(threat_indicators))
    
    def _query_llm(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Query LLM using existing LLMAgent"""
        try:
            response = self.llm_agent.perform_query(
                messages=messages
            )
            
            # perform_query 直接返回字符串结果
            if response:
                return response
            return ""
                
        except Exception as e:
            self.logger.error(f"LLM query failed: {e}")
            return None
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analyze content for threat intelligence
        
        Returns:
            Dictionary with analysis results:
            - threat_indicators: List of threat indicators found
            - step1_output: Entity extraction output
            - step2_output: Relationship analysis output  
            - step3_output: Information verification output
            - error: Error message if failed
        """
        result = {
            'threat_indicators': [],
            'step1_output': None,
            'step2_output': None,
            'step3_output': None,
            'error': None
        }
        
        try:
            # Extract threat indicators
            threat_indicators = self._extract_threat_indicators(content)
            result['threat_indicators'] = threat_indicators
            
            if not threat_indicators:
                result['error'] = "No threat indicators found"
                return result
            
            # Step 1: Extract entities
            messages = [{
                "role": "user", 
                "content": f"""=== SOURCE CONTENT ===
                        {content}

                        === THREAT INDICATORS ===
                        {str(threat_indicators)}

                        === ENTITY DEFINITIONS ===
                        {self.entity_definitions}

                        === EXTRACTION INSTRUCTIONS ===
                        {self.prompts['extract']}"""
            }]
            
            step1_result = self._query_llm(messages)
            if not step1_result:
                result['error'] = "Step 1 failed"
                return result
            result['step1_output'] = step1_result
            
            # Step 2: Analyze relations
            messages = [{
                "role": "user",
                "content": f"""=== SOURCE CONTENT ===
                    {content}

                    === EXTRACTED ENTITIES ===
                    {step1_result}

                    === RELATIONSHIP ANALYSIS INSTRUCTIONS ===
                    {self.prompts['relation']}"""
            }]
            
            step2_result = self._query_llm(messages)
            if not step2_result:
                result['error'] = "Step 2 failed"
                return result
            result['step2_output'] = step2_result
            
            # Step 3: Verify information
            messages = [{
                "role": "user",
                "content": f"""=== SOURCE CONTENT ===
                    {content}

                    === EXTRACTED ENTITIES AND RELATIONS ===
                    {step2_result}

                    === VERIFICATION INSTRUCTIONS ===
                    {self.prompts['verify']}"""
            }]
            
            step3_result = self._query_llm(messages)
            if not step3_result:
                result['error'] = "Step 3 failed"
                return result
            result['step3_output'] = step3_result
            
        except Exception as e:
            result['error'] = str(e)
        
        return result


if __name__ == "__main__":
    # Test
    test_content = """
    CheckPoint研究人员发现了多个恶意PyPI包，这些包模仿了流行的Python库。
    包名为"requestslib"的恶意包模仿了流行的"requests"库。
    另一个名为"numpy-utils"的包也被发现包含恶意代码。
    攻击者使用了evil-domain.com作为C&C服务器。
    """
    
    analyzer = IntelligenceAnalyzer()
    result = analyzer.analyze_content(test_content)
    
    print("Threat indicators:", result['threat_indicators'])
    if result['error']:
        print("Error:", result['error'])
    else:
        print("Step 1 output:", result['step1_output'])
        print("Step 2 output:", result['step2_output']) 
        print("Step 3 output:", result['step3_output'])