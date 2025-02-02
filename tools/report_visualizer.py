from typing import Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import json
import os

class ReportVisualizer:
    def __init__(self):
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / 'templates'
        template_dir.mkdir(exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # Create template files if they don't exist
        self._create_templates()
    
    def _create_templates(self):
        """Create the necessary template files if they don't exist."""
        template_dir = Path(__file__).parent / 'templates'
        
        # Basic HTML template
        basic_template = template_dir / 'basic_report.html'
        if not basic_template.exists():
            basic_template.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>{{ report.title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .report-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .summary {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .finding {
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .source {
            margin-left: 20px;
            font-size: 0.9em;
            color: #666;
        }
        .quote {
            margin: 10px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border-left: 3px solid #ddd;
        }
        .timeline {
            margin: 40px 0;
        }
        .event {
            display: flex;
            margin-bottom: 15px;
        }
        .event-date {
            width: 120px;
            font-weight: bold;
        }
        .event-details {
            flex: 1;
        }
        .metadata {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="report-header">
        <h1>{{ report.title }}</h1>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p>{{ report.summary }}</p>
    </div>
    
    <div class="key-findings">
        <h2>Key Findings</h2>
        {% for finding in report.key_findings %}
        <div class="finding">
            <h3>{{ finding.finding }}</h3>
            {% for source in finding.supporting_sources %}
            <div class="source">
                <a href="{{ source.url }}" target="_blank">{{ source.title }}</a>
                <div class="quote">{{ source.quote }}</div>
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>
    
    <div class="timeline">
        <h2>Timeline of Events</h2>
        {% for event in report.timeline %}
        <div class="event">
            <div class="event-date">{{ event.date }}</div>
            <div class="event-details">
                <strong>{{ event.event }}</strong>
                <p>{{ event.significance }}</p>
            </div>
        </div>
        {% endfor %}
    </div>
    
    <div class="metadata">
        <h3>About this Report</h3>
        <p>Query: {{ report.metadata.query }}</p>
        <p>Sources analyzed: {{ report.metadata.sources_analyzed }}</p>
        <p>Date range: {{ report.metadata.date_range.earliest }} to {{ report.metadata.date_range.latest }}</p>
    </div>
</body>
</html>
""")
        
        # Interactive D3.js template
        d3_template = template_dir / 'd3_report.html'
        if not d3_template.exists():
            d3_template.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>{{ report.title }}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        /* Same CSS as basic template plus D3 specific styles */
        .timeline-viz {
            width: 100%;
            height: 400px;
            margin: 40px 0;
        }
        .findings-network {
            width: 100%;
            height: 600px;
            margin: 40px 0;
        }
    </style>
</head>
<body>
    <!-- Same basic structure as basic template -->
    <div class="report-header">
        <h1>{{ report.title }}</h1>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p>{{ report.summary }}</p>
    </div>
    
    <!-- Interactive timeline visualization -->
    <h2>Interactive Timeline</h2>
    <div id="timeline" class="timeline-viz"></div>
    
    <!-- Interactive findings network -->
    <h2>Findings Network</h2>
    <div id="network" class="findings-network"></div>
    
    <!-- Rest of the report content -->
    <div class="key-findings">
        <h2>Key Findings</h2>
        {% for finding in report.key_findings %}
        <div class="finding">
            <h3>{{ finding.finding }}</h3>
            {% for source in finding.supporting_sources %}
            <div class="source">
                <a href="{{ source.url }}" target="_blank">{{ source.title }}</a>
                <div class="quote">{{ source.quote }}</div>
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>
    
    <div class="metadata">
        <h3>About this Report</h3>
        <p>Query: {{ report.metadata.query }}</p>
        <p>Sources analyzed: {{ report.metadata.sources_analyzed }}</p>
        <p>Date range: {{ report.metadata.date_range.earliest }} to {{ report.metadata.date_range.latest }}</p>
    </div>
    
    <script>
        // Parse the report data
        const report = {{ report|tojson|safe }};
        
        // Timeline Visualization
        function createTimeline() {
            const margin = {top: 20, right: 20, bottom: 30, left: 50};
            const width = document.getElementById('timeline').offsetWidth - margin.left - margin.right;
            const height = 400 - margin.top - margin.bottom;
            
            const svg = d3.select('#timeline')
                .append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', `translate(${margin.left},${margin.top})`);
            
            // Parse dates
            const timelineData = report.timeline.map(d => ({
                ...d,
                dateObj: new Date(d.date)
            }));
            
            // Create scales
            const x = d3.scaleTime()
                .domain(d3.extent(timelineData, d => d.dateObj))
                .range([0, width]);
                
            // Add axis
            svg.append('g')
                .attr('transform', `translate(0,${height})`)
                .call(d3.axisBottom(x));
            
            // Add events
            const events = svg.selectAll('.event')
                .data(timelineData)
                .enter()
                .append('g')
                .attr('class', 'event')
                .attr('transform', d => `translate(${x(d.dateObj)},0)`);
            
            events.append('circle')
                .attr('r', 5)
                .attr('cy', height/2)
                .style('fill', '#4CAF50');
                
            events.append('text')
                .attr('y', height/2 - 10)
                .attr('text-anchor', 'middle')
                .text(d => d.event)
                .call(wrap, 100);
        }
        
        // Findings Network Visualization
        function createNetwork() {
            const width = document.getElementById('network').offsetWidth;
            const height = 600;
            
            const svg = d3.select('#network')
                .append('svg')
                .attr('width', width)
                .attr('height', height);
            
            // Create nodes for findings and sources
            const nodes = [];
            const links = [];
            
            // Add finding nodes
            report.key_findings.forEach((finding, i) => {
                nodes.push({
                    id: `finding-${i}`,
                    type: 'finding',
                    text: finding.finding
                });
                
                // Add source nodes and links
                finding.supporting_sources.forEach((source, j) => {
                    const sourceId = `source-${i}-${j}`;
                    nodes.push({
                        id: sourceId,
                        type: 'source',
                        text: source.title,
                        url: source.url
                    });
                    links.push({
                        source: `finding-${i}`,
                        target: sourceId
                    });
                });
            });
            
            // Create force simulation
            const simulation = d3.forceSimulation(nodes)
                .force('link', d3.forceLink(links).id(d => d.id))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width/2, height/2));
            
            // Add links
            const link = svg.append('g')
                .selectAll('line')
                .data(links)
                .enter()
                .append('line')
                .style('stroke', '#999')
                .style('stroke-width', 1);
            
            // Add nodes
            const node = svg.append('g')
                .selectAll('circle')
                .data(nodes)
                .enter()
                .append('circle')
                .attr('r', d => d.type === 'finding' ? 10 : 5)
                .style('fill', d => d.type === 'finding' ? '#4CAF50' : '#2196F3')
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));
            
            // Add labels
            const label = svg.append('g')
                .selectAll('text')
                .data(nodes)
                .enter()
                .append('text')
                .text(d => d.text)
                .attr('font-size', d => d.type === 'finding' ? '12px' : '10px')
                .attr('dx', 12)
                .attr('dy', 4);
            
            // Add tooltips
            node.append('title')
                .text(d => d.text);
            
            // Update positions
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
                
                label
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            });
            
            // Drag functions
            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            
            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
        }
        
        // Text wrapping function
        function wrap(text, width) {
            text.each(function() {
                const text = d3.select(this);
                const words = text.text().split(/\s+/).reverse();
                let word;
                let line = [];
                let lineNumber = 0;
                const lineHeight = 1.1;
                const y = text.attr('y');
                const dy = parseFloat(text.attr('dy')) || 0;
                let tspan = text.text(null).append('tspan').attr('x', 0).attr('y', y).attr('dy', dy + 'em');
                
                while (word = words.pop()) {
                    line.push(word);
                    tspan.text(line.join(' '));
                    if (tspan.node().getComputedTextLength() > width) {
                        line.pop();
                        tspan.text(line.join(' '));
                        line = [word];
                        tspan = text.append('tspan').attr('x', 0).attr('y', y).attr('dy', ++lineNumber * lineHeight + dy + 'em').text(word);
                    }
                }
            });
        }
        
        // Create visualizations when page loads
        document.addEventListener('DOMContentLoaded', () => {
            createTimeline();
            createNetwork();
        });
    </script>
</body>
</html>
""")
    
    def visualize(self, report: Dict[str, Any], output_dir: str = 'reports', template: str = 'basic_report.html') -> str:
        """
        Generate an HTML visualization of the research report.
        
        Args:
            report: The research report dictionary
            output_dir: Directory to save the HTML file (default: 'reports')
            template: Template to use (default: 'basic_report.html')
            
        Returns:
            Path to the generated HTML file
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate unique filename based on report title
        safe_title = "".join(c for c in report['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}_{report['metadata']['date_range']['latest']}.html"
        output_file = output_path / filename
        
        # Render template
        template = self.env.get_template(template)
        html = template.render(report=report)
        
        # Save to file
        output_file.write_text(html)
        
        return str(output_file) 