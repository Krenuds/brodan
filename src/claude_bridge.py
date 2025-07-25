"""
Claude Code Bridge - Integration between Discord voice bot and Claude Code

This module handles routing Discord voice input to Claude Code's CLI interface
and returns the response for TTS playback in Discord.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ClaudeBridge:
    """Bridge between Discord voice bot and Claude Code CLI"""
    
    def __init__(self):
        self.proxy_url = "http://localhost:8001"
        self.session_id = None
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def process_voice_input(self, input_text: str) -> str:
        """
        Process voice input through Claude Code and return response
        
        Args:
            input_text: Transcribed voice input from Discord
            
        Returns:
            Claude's response text for TTS synthesis
        """
        try:
            # Clean and prepare input
            cleaned_input = input_text.strip()
            if not cleaned_input:
                return "I didn't catch that, could you repeat?"
            
            logger.info(f"Processing voice input: {cleaned_input}")
            
            # Check if this is a command or conversation
            if self._is_command(cleaned_input):
                response = await self._execute_claude_command(cleaned_input)
            else:
                response = await self._claude_conversation(cleaned_input)
            
            # Limit response length for voice
            response = self._format_for_voice(response)
            
            logger.info(f"Claude response: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _is_command(self, text: str) -> bool:
        """
        Determine if input is a command or general conversation
        
        Command patterns:
        - "create a file..."
        - "run the tests"
        - "edit the config"
        - "search for..."
        """
        command_keywords = [
            "create", "make", "build", "run", "execute", "test", "edit", "modify", 
            "update", "delete", "remove", "search", "find", "grep", "install",
            "commit", "push", "pull", "deploy", "start", "stop", "restart"
        ]
        
        words = text.lower().split()
        return any(keyword in words for keyword in command_keywords)
    
    async def _execute_claude_command(self, command: str) -> str:
        """Execute command through Claude Code CLI with tool access"""
        try:
            # Execute the command using Claude Code CLI
            logger.info(f"Executing Claude command: {command}")
            
            # Run claude CLI in non-interactive mode with the command
            process = await asyncio.create_subprocess_exec(
                'claude', 
                '--non-interactive',
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd='/home/travis/brodan'  # Ensure we're in the project directory
            )
            
            # Set timeout for Claude CLI execution (30 seconds)
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return "Command timed out after 30 seconds."
            
            if process.returncode == 0:
                response = stdout.decode('utf-8').strip()
                if not response:
                    return "Command completed successfully."
                return response
            else:
                error_msg = stderr.decode('utf-8').strip()
                logger.error(f"Claude CLI error (return code {process.returncode}): {error_msg}")
                
                # Provide more user-friendly error messages
                if "command not found" in error_msg.lower():
                    return "Claude Code CLI is not installed or not in PATH."
                elif "permission denied" in error_msg.lower():
                    return "Permission denied when executing command."
                elif error_msg:
                    return f"Command error: {error_msg}"
                else:
                    return f"Command failed with exit code {process.returncode}."
                
        except FileNotFoundError:
            logger.error("Claude CLI not found")
            return "Claude Code CLI is not installed. Please install Claude Code first."
        except Exception as e:
            logger.error(f"Error executing Claude command: {e}")
            return f"Failed to execute command: {str(e)}"
    
    async def _claude_conversation(self, message: str) -> str:
        """Handle general conversation with Claude"""
        try:
            # Use Claude Code CLI for general conversation
            logger.info(f"Processing conversation: {message}")
            
            # Run claude CLI in non-interactive mode for conversation
            process = await asyncio.create_subprocess_exec(
                'claude', 
                '--non-interactive',
                message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd='/home/travis/brodan'  # Ensure we're in the project directory
            )
            
            # Set timeout for conversation (20 seconds)
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=20.0
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return "My response timed out. Could you try rephrasing your question?"
            
            if process.returncode == 0:
                response = stdout.decode('utf-8').strip()
                if not response:
                    return "I don't have a response for that."
                return response
            else:
                error_msg = stderr.decode('utf-8').strip()
                logger.error(f"Claude CLI conversation error (return code {process.returncode}): {error_msg}")
                
                # Provide more user-friendly error messages
                if "command not found" in error_msg.lower():
                    return "Claude Code CLI is not available for conversation."
                elif error_msg:
                    return f"I encountered an error: {error_msg}"
                else:
                    return "I encountered an unexpected error processing your message."
                
        except FileNotFoundError:
            logger.error("Claude CLI not found for conversation")
            return "Claude Code CLI is not installed. I can't process your message."
        except Exception as e:
            logger.error(f"Error in Claude conversation: {e}")
            return "I encountered an error processing your message."
    
    def _format_for_voice(self, text: str) -> str:
        """Format Claude's response for voice synthesis"""
        if not text:
            return "I don't have a response for that."
        
        # Limit length for voice (roughly 30 seconds at normal speaking pace)
        max_chars = 500
        if len(text) > max_chars:
            # Try to cut at a sentence boundary
            sentences = text.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence) > max_chars:
                    break
                truncated += sentence + ". "
            
            if truncated:
                text = truncated.strip()
            else:
                text = text[:max_chars] + "..."
        
        # Clean up common formatting issues for voice
        text = text.replace('\n', ' ')  # Remove line breaks
        text = text.replace('  ', ' ')  # Remove double spaces
        text = self._replace_code_references(text)
        
        return text.strip()
    
    def _replace_code_references(self, text: str) -> str:
        """Replace code references with voice-friendly versions"""
        replacements = {
            '`': '',  # Remove backticks
            '```': '',  # Remove code blocks
            'src/': 'source ',
            '.py': ' python file',
            '.js': ' javascript file',
            '.json': ' json file',
            '.md': ' markdown file',
            '->': ' to ',
            '=>': ' to ',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def set_session_id(self, session_id: str):
        """Set session ID for conversation continuity"""
        self.session_id = session_id
        logger.info(f"Set Claude session ID: {session_id}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge status information"""
        return {
            "proxy_url": self.proxy_url,
            "session_id": self.session_id,
            "connected": True
        }