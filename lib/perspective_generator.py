"""
OmniFocus Perspective Generator

Creates OmniFocus perspective plist files that can be imported by double-clicking.
Based on analysis of exported perspective structure.
"""

import io
import json
import logging
import plistlib
import os
from typing import Dict, Any, Optional
from pathlib import Path


class PerspectiveGenerator:
    """Generates OmniFocus perspective plist files from templates."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_colleague_perspective_plist(
        self, 
        colleague_name: str, 
        colleague_tag_id: str,
        template_path: str,
        output_dir: str = "./perspectives"
    ) -> str:
        """
        Create a new perspective plist file for a colleague from XML template.
        
        Args:
            colleague_name: Name of the colleague (becomes perspective name)
            colleague_tag_id: OmniFocus tag ID for the colleague
            template_path: Path to the template XML file
            output_dir: Directory to save the generated plist
            
        Returns:
            Path to the generated plist file
        """
        try:
            self.logger.info(f"Generating perspective plist for {colleague_name}")
            
            # Read template XML and replace placeholders
            template_xml = self._read_template_xml(template_path)
            processed_xml = self._replace_placeholders(template_xml, colleague_name, colleague_tag_id)
            
            # Convert XML to plist data
            plist_data = self._xml_to_plist_data(processed_xml)
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output file path
            safe_name = self._sanitize_filename(colleague_name)
            output_file = os.path.join(output_dir, f"{safe_name}.ofocus-perspective", "Info-v3.plist")
            
            # Create perspective directory
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Write the plist file
            self._write_plist_file(output_file, plist_data)
            
            self.logger.info(f"✅ Created perspective plist: {output_file}")
            self.logger.info(f"📁 To import: Double-click the .ofocus-perspective folder")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Failed to create perspective plist: {e}")
            raise
    
    def _read_template_xml(self, template_path: str) -> str:
        """Read the template XML file."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read template XML: {e}")
    
    def _replace_placeholders(self, xml_content: str, colleague_name: str, colleague_tag_id: str) -> str:
        """Replace placeholders in XML content."""
        try:
            # Replace the placeholders
            processed_xml = xml_content
            processed_xml = processed_xml.replace('#perspectiveName', colleague_name)
            processed_xml = processed_xml.replace('#personTagId', colleague_tag_id)
            
            self.logger.debug(f"Replaced placeholders: name='{colleague_name}', tag_id='{colleague_tag_id}'")
            return processed_xml
            
        except Exception as e:
            raise ValueError(f"Failed to replace placeholders: {e}")
    
    def _xml_to_plist_data(self, xml_content: str) -> Dict[str, Any]:
        """Convert XML content to plist data structure."""
        try:
            # Parse the XML content using plistlib
            xml_bytes = xml_content.encode('utf-8')
            return plistlib.load(io.BytesIO(xml_bytes))
        except Exception as e:
            raise ValueError(f"Failed to convert XML to plist data: {e}")
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize colleague name for use in filename."""
        # Replace spaces and special characters with underscores
        safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
        return safe_name.strip('_')
    
    def _write_plist_file(self, output_path: str, data: Dict[str, Any]) -> None:
        """Write data to plist file in binary format."""
        try:
            with open(output_path, 'wb') as f:
                plistlib.dump(data, f, fmt=plistlib.FMT_BINARY)
        except Exception as e:
            raise ValueError(f"Failed to write plist file: {e}")
    
    def analyze_template_tags(self, template_path: str) -> Dict[str, Any]:
        """Analyze template XML to show tag structure (for debugging)."""
        try:
            xml_content = self._read_template_xml(template_path)
            template_data = self._xml_to_plist_data(xml_content)
            filter_rules = json.loads(template_data.get('filterRules', '[]'))
            
            analysis = {
                'name': template_data.get('name'),
                'version': template_data.get('version'),
                'aggregation': template_data.get('topLevelFilterAggregation'),
                'placeholders': [],
                'tag_ids': set(),
                'rules_structure': []
            }
            
            # Check for placeholders in the original XML
            if '#perspectiveName' in xml_content:
                analysis['placeholders'].append('#perspectiveName')
            if '#personTagId' in xml_content:
                analysis['placeholders'].append('#personTagId')
            
            for rule in filter_rules:
                rule_info = {
                    'type': rule.get('aggregateType'),
                    'conditions': []
                }
                
                if 'aggregateRules' in rule:
                    for aggregate_rule in rule['aggregateRules']:
                        for key, value in aggregate_rule.items():
                            if key in ['actionHasAllOfTags', 'actionHasAnyOfTags']:
                                analysis['tag_ids'].update(value)
                            rule_info['conditions'].append({key: value})
                
                analysis['rules_structure'].append(rule_info)
            
            analysis['tag_ids'] = list(analysis['tag_ids'])
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze template: {e}")
            raise
