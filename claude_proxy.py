#!/usr/bin/env python3
"""
Claude Code Proxy Server

This runs on the host and provides an HTTP API for Docker containers
to interact with Claude Code CLI.
"""

import asyncio
import json
import logging
import subprocess
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Claude Code Proxy",
    description="HTTP proxy for Claude Code CLI integration",
    version="1.0.0"
)

class ClaudeRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    is_command: bool = False

class ClaudeResponse(BaseModel):
    response: str
    session_id: str
    success: bool
    error: Optional[str] = None

class ClaudeProxy:
    def __init__(self):
        self.claude_path = "/usr/local/bin/claude"
        self.active_sessions = {}
        
    async def process_request(self, request: ClaudeRequest) -> ClaudeResponse:
        """Process Claude Code request"""
        try:
            # Generate session ID if not provided
            session_id = request.session_id or str(uuid.uuid4())
            
            # Build Claude command
            cmd = [
                self.claude_path,
                "--print",
                "--output-format", "text"
            ]
            
            # Add tool permissions for commands
            if request.is_command:
                cmd.extend([
                    "--allowedTools", 
                    "Bash,Edit,Write,Read,Grep,Glob,LS,WebFetch,WebSearch"
                ])
            
            # Add session continuity
            if session_id in self.active_sessions:
                cmd.extend(["--continue"])
            
            # Add the text prompt
            cmd.append(request.text)
            
            logger.info(f"Executing Claude command for session {session_id}")
            
            # Execute Claude CLI
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/home/travis/brodan"
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=30.0
            )
            
            # Track active session
            self.active_sessions[session_id] = True
            
            if process.returncode == 0:
                response_text = stdout.decode('utf-8', errors='ignore').strip()
                if not response_text:
                    response_text = "Task completed successfully."
                
                return ClaudeResponse(
                    response=response_text,
                    session_id=session_id,
                    success=True
                )
            else:
                error_msg = stderr.decode('utf-8', errors='ignore').strip()
                logger.error(f"Claude command failed: {error_msg}")
                
                return ClaudeResponse(
                    response="I encountered an error processing that request.",
                    session_id=session_id,
                    success=False,
                    error=error_msg
                )
                
        except asyncio.TimeoutError:
            return ClaudeResponse(
                response="That request is taking too long to process.",
                session_id=session_id,
                success=False,
                error="Timeout"
            )
        except Exception as e:
            logger.error(f"Error processing Claude request: {e}")
            return ClaudeResponse(
                response="I'm having trouble processing that right now.",
                session_id=session_id,
                success=False,
                error=str(e)
            )

# Global proxy instance
proxy = ClaudeProxy()

@app.post("/claude", response_model=ClaudeResponse)
async def process_claude_request(request: ClaudeRequest):
    """Process a Claude Code request"""
    return await proxy.process_request(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "claude_available": True}

@app.get("/sessions")
async def list_sessions():
    """List active sessions"""
    return {"active_sessions": list(proxy.active_sessions.keys())}

if __name__ == "__main__":
    print("🚀 Starting Claude Code Proxy Server on port 8001")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )