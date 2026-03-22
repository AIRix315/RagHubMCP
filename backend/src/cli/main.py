"""RagHubMCP CLI - Command Line Interface for RAG operations.

This module provides command-line tools for:
- Quick querying with profile support
- Provider management (list, test, switch)
- Profile configuration
- Pipeline debugging

Reference: Docs/22-Config-API-Design.md Section 3.4
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()


# =============================================================================
# Shared context for CLI commands
# =============================================================================

class CLIContext:
    """CLI context with configuration and API client."""
    
    def __init__(self):
        self.config = None
        self.api_base = "http://localhost:8818"
        self._client = None
    
    @property
    def client(self):
        """Get HTTP client (lazy load)."""
        if self._client is None:
            import httpx
            self._client = httpx.Client(base_url=self.api_base, timeout=30.0)
        return self._client


pass_context = click.make_pass_decorator(CLIContext, ensure=True)


# =============================================================================
# Main CLI Group
# =============================================================================

@click.group()
@click.option('--api-base', default='http://localhost:8818', help='API base URL')
@click.version_option(version='2.3.1', prog_name='raghub')
@click.pass_context
def cli(ctx: click.Context, api_base: str):
    """RagHubMCP - Universal Code RAG Hub CLI.
    
    Quick Start:
        raghub query "your query"          # Quick query
        raghub provider list                # List providers
        raghub config apply fast            # Apply profile
    
    Run 'raghub COMMAND --help' for more information.
    """
    ctx.obj = CLIContext()
    ctx.obj.api_base = api_base


# =============================================================================
# Query Command
# =============================================================================

@cli.command()
@click.argument('query')
@click.option('--profile', '-p', default='balanced', 
              type=click.Choice(['fast', 'balanced', 'accurate']),
              help='Use specified profile (fast/balanced/accurate)')
@click.option('--top-k', '-k', default=5, type=int,
              help='Number of results to return')
@click.option('--output', '-o', default='table',
              type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--debug', is_flag=True, help='Show debug information')
@pass_context
def query(ctx: CLIContext, query: str, profile: str, top_k: int, output: str, debug: bool):
    """Query the knowledge base.
    
    Examples:
        raghub query "machine learning basics"
        raghub query "neural networks" --profile accurate --top-k 10
        raghub query "API design" --output json
    """
    try:
        console.print(f"[bold blue]Query:[/] {query}")
        console.print(f"[dim]Profile: {profile}, Top-K: {top_k}[/]")
        
        # Make API request
        response = ctx.client.post('/api/query', json={
            'query': query,
            'profile': profile,
            'top_k': top_k,
            'debug': debug,
        })
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code} - {response.text}[/]")
            sys.exit(1)
        
        data = response.json()
        
        if output == 'json':
            console.print_json(json.dumps(data, indent=2))
        else:
            _display_results(data, output, debug)
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


def _display_results(data: dict[str, Any], output: str, debug: bool):
    """Display query results in table format."""
    results = data.get('results', [])
    latency_ms = data.get('latency_ms', 0)
    
    if not results:
        console.print("[yellow]No results found.[/]")
        return
    
    # Create table
    table = Table(title=f"Results ({len(results)} results, {latency_ms:.2f}ms)")
    table.add_column("#", style="dim", width=4)
    table.add_column("Score", justify="right", style="green")
    table.add_column("Text", width=80)
    table.add_column("Source", style="dim")
    
    for i, result in enumerate(results, 1):
        score = result.get('score', 0)
        text = result.get('text', '')[:100] + ('...' if len(result.get('text', '')) > 100 else '')
        source = result.get('metadata', {}).get('source', 'N/A')
        
        # Color based on score
        score_style = "green" if score >= 0.8 else "yellow" if score >= 0.5 else "red"
        
        table.add_row(
            str(i),
            f"[{score_style}]{score:.4f}[/{score_style}]",
            text,
            source,
        )
    
    console.print(table)
    
    # Show debug info if requested
    if debug and 'debug_info' in data:
        _display_debug_info(data['debug_info'])


def _display_debug_info(debug_info: dict[str, Any]):
    """Display debug information."""
    console.print("\n[bold yellow]Debug Information:[/]")
    
    stages = debug_info.get('stages', [])
    for stage in stages:
        name = stage.get('name', 'unknown')
        latency = stage.get('latency_ms', 0)
        status = stage.get('status', 'unknown')
        
        status_icon = "✓" if status == "completed" else "✗" if status == "error" else "○"
        console.print(f"  {status_icon} [bold]{name}[/]: {latency:.2f}ms")


# =============================================================================
# Provider Command Group
# =============================================================================

@cli.group()
def provider():
    """Manage providers (embedding, rerank, vectorstore)."""
    pass


@provider.command('list')
@click.option('--type', '-t', 'provider_type', default=None,
              type=click.Choice(['embedding', 'rerank', 'vectorstore']),
              help='Filter by provider type')
@click.option('--output', '-o', default='table',
              type=click.Choice(['table', 'json']),
              help='Output format')
@pass_context
def provider_list(ctx: CLIContext, provider_type: str | None, output: str):
    """List all providers or filter by type.
    
    Examples:
        raghub provider list
        raghub provider list --type rerank
    """
    try:
        endpoint = f'/api/providers/{provider_type}' if provider_type else '/api/providers'
        response = ctx.client.get(endpoint)
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/]")
            sys.exit(1)
        
        data = response.json()
        
        if output == 'json':
            console.print_json(json.dumps(data, indent=2))
        else:
            _display_providers(data, provider_type)
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


def _display_providers(data: list[dict] | dict, provider_type: str | None):
    """Display providers in table format."""
    # Handle nested provider types
    if isinstance(data, dict) and provider_type is None:
        # All providers, grouped by type
        for ptype, providers in data.items():
            if providers:
                console.print(f"\n[bold]{ptype.upper()}[/]")
                _display_provider_table(providers)
    else:
        # Single provider type
        providers = data if isinstance(data, list) else [data]
        _display_provider_table(providers)


def _display_provider_table(providers: list[dict]):
    """Display a table of providers."""
    table = Table()
    table.add_column("Name", style="bold")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Default", justify="center")
    
    for p in providers:
        name = p.get('name', 'N/A')
        ptype = p.get('type', 'N/A')
        status = p.get('status', 'unknown')
        is_default = "✓" if p.get('is_default', False) else ""
        
        status_style = "green" if status == "active" else "yellow" if status == "inactive" else "red"
        
        table.add_row(name, ptype, f"[{status_style}]{status}[/{status_style}]", is_default)
    
    console.print(table)


@provider.command('test')
@click.argument('name')
@click.option('--type', '-t', 'provider_type', default='rerank',
              type=click.Choice(['embedding', 'rerank', 'vectorstore']),
              help='Provider type')
@click.option('--query', '-q', default='test query',
              help='Test query')
@pass_context
def provider_test(ctx: CLIContext, name: str, provider_type: str, query: str):
    """Test a provider connection.
    
    Examples:
        raghub provider test onnx-minilm --type rerank
        raghub provider test ollama-bge --type embedding -q "hello world"
    """
    try:
        console.print(f"[bold]Testing {provider_type} provider:[/] {name}")
        
        endpoint = f'/api/providers/{provider_type}/{name}/test'
        response = ctx.client.post(endpoint, json={'query': query})
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/]")
            sys.exit(1)
        
        data = response.json()
        
        success = data.get('success', False)
        latency = data.get('latency_ms', 0)
        message = data.get('message', '')
        
        if success:
            console.print(f"[green]✓ Test successful[/]")
            console.print(f"  Latency: {latency:.2f}ms")
            if message:
                console.print(f"  Message: {message}")
        else:
            console.print(f"[red]✗ Test failed[/]")
            console.print(f"  Error: {message}")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


@provider.command('switch')
@click.argument('name')
@click.option('--type', '-t', 'provider_type', default='rerank',
              type=click.Choice(['embedding', 'rerank', 'vectorstore']),
              help='Provider type')
@pass_context
def provider_switch(ctx: CLIContext, name: str, provider_type: str):
    """Set default provider.
    
    Examples:
        raghub provider switch onnx-minilm --type rerank
    """
    try:
        endpoint = f'/api/providers/{provider_type}/{name}/set-default'
        response = ctx.client.post(endpoint)
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/]")
            sys.exit(1)
        
        console.print(f"[green]✓ Switched default {provider_type} provider to:[/] {name}")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


# =============================================================================
# Config Command Group
# =============================================================================

@cli.group()
def config():
    """Configuration management."""
    pass


@config.command('list')
@click.option('--all', 'show_all', is_flag=True, help='Show all config including defaults')
@pass_context
def config_list(ctx: CLIContext, show_all: bool):
    """List current configuration.
    
    Examples:
        raghub config list
        raghub config list --all
    """
    try:
        response = ctx.client.get('/api/config')
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/]")
            sys.exit(1)
        
        data = response.json()
        console.print_json(json.dumps(data, indent=2))
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


@config.command('profiles')
@pass_context
def config_profiles(ctx: CLIContext):
    """List available profiles.
    
    Examples:
        raghub config profiles
    """
    try:
        response = ctx.client.get('/api/profiles')
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/]")
            sys.exit(1)
        
        profiles = response.json()
        
        table = Table(title="Available Profiles")
        table.add_column("Name", style="bold")
        table.add_column("Description")
        table.add_column("Default", justify="center")
        table.add_column("Active", justify="center")
        
        for p in profiles:
            name = p.get('name', 'N/A')
            description = p.get('description', 'N/A')
            is_default = "✓" if p.get('is_default', False) else ""
            is_active = "✓" if p.get('is_active', False) else ""
            
            table.add_row(name, description, is_default, is_active)
        
        console.print(table)
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


@config.command('apply')
@click.argument('profile', type=click.Choice(['fast', 'balanced', 'accurate']))
@pass_context
def config_apply(ctx: CLIContext, profile: str):
    """Apply a profile configuration.
    
    Examples:
        raghub config apply fast
        raghub config apply accurate
    """
    try:
        console.print(f"[bold]Applying profile:[/] {profile}")
        
        endpoint = f'/api/profiles/{profile}/apply'
        response = ctx.client.post(endpoint)
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/]")
            sys.exit(1)
        
        data = response.json()
        previous = data.get('previous_profile', '')
        message = data.get('message', '')
        
        console.print(f"[green]✓ {message}[/]")
        if previous:
            console.print(f"  Previous: {previous}")
        console.print(f"  Current: {profile}")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


# =============================================================================
# Pipeline Command Group
# =============================================================================

@cli.group()
def pipeline():
    """Pipeline operations and debugging."""
    pass


@pipeline.command('test')
@click.option('--query', '-q', default='test query', help='Test query')
@click.option('--profile', '-p', default='balanced',
              type=click.Choice(['fast', 'balanced', 'accurate']),
              help='Profile to use')
@pass_context
def pipeline_test(ctx: CLIContext, query: str, profile: str):
    """Test pipeline execution.
    
    Examples:
        raghub pipeline test -q "machine learning"
        raghub pipeline test --profile accurate
    """
    try:
        console.print(f"[bold]Testing pipeline with profile:[/] {profile}")
        console.print(f"[dim]Query: {query}[/]")
        
        response = ctx.client.post('/api/query', json={
            'query': query,
            'profile': profile,
            'top_k': 5,
        })
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/]")
            sys.exit(1)
        
        data = response.json()
        
        console.print(f"\n[green]✓ Pipeline test successful[/]")
        console.print(f"  Results: {len(data.get('results', []))} documents")
        console.print(f"  Latency: {data.get('latency_ms', 0):.2f}ms")
        console.print(f"  Profile: {data.get('profile_used', 'N/A')}")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


@pipeline.command('debug')
@click.argument('query')
@click.option('--profile', '-p', default='balanced',
              type=click.Choice(['fast', 'balanced', 'accurate']),
              help='Profile to use')
@pass_context
def pipeline_debug(ctx: CLIContext, query: str, profile: str):
    """Debug pipeline execution with detailed output.
    
    Shows intermediate states for each pipeline stage.
    
    Examples:
        raghub pipeline debug "machine learning algorithms"
        raghub pipeline debug "API design" --profile accurate
    """
    try:
        console.print(f"[bold blue]Pipeline Debug Mode[/]")
        console.print(f"[dim]Query: {query}[/]")
        console.print(f"[dim]Profile: {profile}[/]\n")
        
        # Create debug query
        create_response = ctx.client.post('/api/debug/pipeline', json={
            'query': query,
            'documents': ['Sample document 1', 'Sample document 2'],
            'config': {'profile': profile},
        })
        
        if create_response.status_code != 200:
            console.print(f"[red]Error creating debug query: {create_response.status_code}[/]")
            sys.exit(1)
        
        query_id = create_response.json().get('query_id')
        console.print(f"[dim]Query ID: {query_id}[/]\n")
        
        # Simulate execution
        sim_response = ctx.client.post(f'/api/debug/pipeline/{query_id}/simulate')
        
        if sim_response.status_code != 200:
            console.print(f"[red]Error simulating execution: {sim_response.status_code}[/]")
            sys.exit(1)
        
        # Get debug info
        debug_response = ctx.client.get(f'/api/debug/pipeline/{query_id}')
        
        if debug_response.status_code != 200:
            console.print(f"[red]Error getting debug info: {debug_response.status_code}[/]")
            sys.exit(1)
        
        debug_info = debug_response.json()
        
        # Display debug information
        _display_pipeline_debug(debug_info)
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


def _display_pipeline_debug(debug_info: dict[str, Any]):
    """Display detailed pipeline debug information."""
    query_id = debug_info.get('query_id', 'unknown')
    stages = debug_info.get('stages', [])
    
    console.print(f"[bold]Pipeline Execution[/]")
    console.print(f"[dim]Query ID: {query_id}[/]\n")
    
    for stage in stages:
        name = stage.get('name', 'unknown')
        status = stage.get('status', 'unknown')
        latency = stage.get('latency_ms', 0)
        input_data = stage.get('input', {})
        output_data = stage.get('output', {})
        metadata = stage.get('metadata', {})
        
        status_icon = "✓" if status == "completed" else "✗" if status == "error" else "○"
        status_style = "green" if status == "completed" else "red" if status == "error" else "yellow"
        
        console.print(f"[{status_style}]{status_icon} Stage: {name}[/{status_style}] ({latency:.2f}ms)")
        
        if metadata:
            console.print(f"  [dim]Metadata:[/]")
            for key, value in metadata.items():
                console.print(f"    {key}: {value}")
        
        if output_data:
            console.print(f"  [dim]Output:[/]")
            for key, value in output_data.items():
                console.print(f"    {key}: {value}")
        
        console.print()


# =============================================================================
# Status Command
# =============================================================================

@cli.command('status')
@click.option('--output', '-o', default='table',
              type=click.Choice(['table', 'json']),
              help='Output format')
@pass_context
def status(ctx: CLIContext, output: str):
    """Show system status.
    
    Examples:
        raghub status
        raghub status --output json
    """
    try:
        # Get health check
        health_response = ctx.client.get('/health')
        
        if health_response.status_code != 200:
            console.print(f"[red]✗ Server not responding[/]")
            sys.exit(1)
        
        health = health_response.json()
        
        if output == 'json':
            console.print_json(json.dumps(health, indent=2))
        else:
            console.print("[green]✓ Server is healthy[/]")
            console.print(f"  Version: {health.get('version', 'N/A')}")
            console.print(f"  Service: {health.get('service', 'N/A')}")
        
        # Get active profile
        try:
            profiles_response = ctx.client.get('/api/profiles/active')
            if profiles_response.status_code == 200:
                active_profile = profiles_response.json()
                console.print(f"\n[bold]Active Profile:[/] {active_profile.get('name', 'N/A')}")
                console.print(f"  {active_profile.get('description', '')}")
        except Exception:
            pass
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()