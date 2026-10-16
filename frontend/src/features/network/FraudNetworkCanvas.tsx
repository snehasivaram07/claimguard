import React, { useEffect, useRef, useState, useCallback } from 'react';
import cytoscape from 'cytoscape';
import type { Core, EventObject, LayoutOptions } from 'cytoscape';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCw,
  Sliders,
  Target,
} from 'lucide-react';
import type { FraudRingNode, FraudRingEdge } from '../../types';

interface FraudNetworkCanvasProps {
  nodes: FraudRingNode[];
  edges: FraudRingEdge[];
  onSelectNode: (node: FraudRingNode | null) => void;
  onSelectEdge: (edge: FraudRingEdge | null) => void;
  selectedNodeId?: string | null;
  nodeTypeFilter?: string;
  searchTerm?: string;
}

type LayoutName = 'cose' | 'concentric' | 'circle' | 'breadthfirst';

export const FraudNetworkCanvas: React.FC<FraudNetworkCanvasProps> = ({
  nodes,
  edges,
  onSelectNode,
  onSelectEdge,
  selectedNodeId,
  nodeTypeFilter = 'all',
  searchTerm = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [currentLayout, setCurrentLayout] = useState<LayoutName>('cose');
  const [nodeCount, setNodeCount] = useState<number>(0);
  const [edgeCount, setEdgeCount] = useState<number>(0);

  // Check if dark mode is active
  const isDarkMode = typeof window !== 'undefined' && document.documentElement.classList.contains('dark');

  // Build Layout config
  const getLayoutConfig = useCallback((name: LayoutName): LayoutOptions => {
    switch (name) {
      case 'concentric':
        return {
          name: 'concentric',
          concentric: (node: { data: (key: string) => unknown }) => {
            if (node.data('is_target')) return 4;
            if (node.data('type') === 'person') return 3;
            if (node.data('type') === 'organization') return 2;
            return 1;
          },
          levelWidth: () => 1,
          padding: 40,
          animate: true,
          animationDuration: 500,
        };
      case 'circle':
        return {
          name: 'circle',
          padding: 40,
          animate: true,
          animationDuration: 500,
        };
      case 'breadthfirst':
        return {
          name: 'breadthfirst',
          directed: true,
          padding: 40,
          animate: true,
          animationDuration: 500,
        };
      case 'cose':
      default:
        return {
          name: 'cose',
          animate: true,
          animationDuration: 600,
          nodeRepulsion: () => 600000,
          idealEdgeLength: () => 110,
          edgeElasticity: () => 100,
          gravity: 0.2,
          numIter: 1000,
          padding: 50,
        };
    }
  }, []);

  // Initialize or re-render Cytoscape
  useEffect(() => {
    if (!containerRef.current) return;

    // Filter nodes if filter is active
    const filteredNodes = nodes.filter((n) => {
      if (nodeTypeFilter === 'all') return true;
      if (n.is_target) return true; // always show focal target
      return n.type === nodeTypeFilter;
    });

    const activeNodeIds = new Set(filteredNodes.map((n) => n.id));

    // Keep only edges between active nodes
    const filteredEdges = edges.filter(
      (e) => activeNodeIds.has(e.source) && activeNodeIds.has(e.target)
    );

    setNodeCount(filteredNodes.length);
    setEdgeCount(filteredEdges.length);

    // Transform elements for cytoscape
    const elements: cytoscape.ElementDefinition[] = [
      ...filteredNodes.map((n) => ({
        group: 'nodes' as const,
        data: {
          id: n.id,
          label: n.label,
          type: n.type,
          is_target: !!n.is_target,
          rawNode: n,
        },
      })),
      ...filteredEdges.map((e, idx) => ({
        group: 'edges' as const,
        data: {
          id: `e-${e.source}-${e.target}-${idx}`,
          source: e.source,
          target: e.target,
          type: e.type,
          rawEdge: e,
        },
      })),
    ];

    // Theme palette
    const textColor = isDarkMode ? '#f8fafc' : '#0f172a';
    const edgeColor = isDarkMode ? '#334155' : '#cbd5e1';
    const edgeLabelColor = isDarkMode ? '#94a3b8' : '#64748b';

    // Destroy existing instance
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        // Base Node Style
        {
          selector: 'node',
          style: {
            content: 'data(label)',
            'font-size': '11px',
            'font-weight': 'bold',
            color: textColor,
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'text-wrap': 'ellipsis',
            'text-max-width': '110px',
            'background-color': '#1e293b',
            'border-width': 2,
            'border-color': '#475569',
            width: 38,
            height: 38,
            'transition-property': 'background-color, border-color, border-width, width, height',
            'transition-duration': 0.2,
          },
        },
        // Focal Target Claim Node (Distinctive Diamond / Glow)
        {
          selector: 'node[?is_target]',
          style: {
            shape: 'diamond',
            width: 54,
            height: 54,
            'background-color': '#0284c7',
            'border-width': 4,
            'border-color': '#38bdf8',
            'font-size': '12px',
            'font-weight': 'bold',
            color: '#38bdf8',
            'z-index': 100,
          },
        },
        // Connected External Claims
        {
          selector: 'node[type = "claim"][!is_target]',
          style: {
            shape: 'round-rectangle',
            width: 42,
            height: 42,
            'background-color': '#0f172a',
            'border-width': 2,
            'border-color': '#64748b',
          },
        },
        // Persons (Claimants, Drivers, Doctors)
        {
          selector: 'node[type = "person"]',
          style: {
            shape: 'ellipse',
            width: 38,
            height: 38,
            'background-color': '#059669',
            'border-width': 2,
            'border-color': '#34d399',
          },
        },
        // Organizations (Repair Facilities, Clinics, Law Firms)
        {
          selector: 'node[type = "organization"]',
          style: {
            shape: 'hexagon',
            width: 44,
            height: 44,
            'background-color': '#7c3aed',
            'border-width': 2,
            'border-color': '#c084fc',
          },
        },
        // Selected Node Highlight
        {
          selector: 'node:selected, node.selected',
          style: {
            'border-width': 4,
            'border-color': '#f59e0b',
            'underlay-color': '#f59e0b',
            'underlay-padding': 4,
            'underlay-opacity': 0.5,
            'z-index': 150,
          },
        },
        // Search Filter Highlighted
        {
          selector: 'node.search-match',
          style: {
            'border-width': 5,
            'border-color': '#f43f5e',
            'underlay-color': '#f43f5e',
            'underlay-padding': 6,
            'underlay-opacity': 0.6,
          },
        },
        // Base Edge Style
        {
          selector: 'edge',
          style: {
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'line-color': edgeColor,
            'target-arrow-color': edgeColor,
            width: 1.5,
            'arrow-scale': 0.8,
            'font-size': '9px',
            'font-family': 'monospace',
            color: edgeLabelColor,
            label: 'data(type)',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
            'transition-property': 'line-color, width, target-arrow-color',
            'transition-duration': 0.2,
          },
        },
        // Selected Edge Highlight
        {
          selector: 'edge:selected, edge.selected',
          style: {
            width: 3,
            'line-color': '#38bdf8',
            'target-arrow-color': '#38bdf8',
            color: '#38bdf8',
            'font-weight': 'bold',
            'z-index': 90,
          },
        },
      ],
      layout: getLayoutConfig(currentLayout),
      minZoom: 0.3,
      maxZoom: 3.5,
      wheelSensitivity: 0.25,
    });

    // Event: Node Tap
    cy.on('tap', 'node', (evt: EventObject) => {
      const rawNode = evt.target.data('rawNode') as FraudRingNode;
      onSelectNode(rawNode);
      onSelectEdge(null);
    });

    // Event: Edge Tap
    cy.on('tap', 'edge', (evt: EventObject) => {
      const rawEdge = evt.target.data('rawEdge') as FraudRingEdge;
      onSelectEdge(rawEdge);
      onSelectNode(null);
    });

    // Event: Background Tap (Deselect)
    cy.on('tap', (evt: EventObject) => {
      if (evt.target === cy) {
        onSelectNode(null);
        onSelectEdge(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [nodes, edges, nodeTypeFilter, isDarkMode, currentLayout, getLayoutConfig, onSelectNode, onSelectEdge]);

  // Handle External Selection Highlight
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;
    cy.nodes().removeClass('selected');
    if (selectedNodeId) {
      const targetNode = cy.getElementById(selectedNodeId);
      if (targetNode && targetNode.length > 0) {
        targetNode.addClass('selected');
      }
    }
  }, [selectedNodeId]);

  // Handle Search Highlighting
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;
    cy.nodes().removeClass('search-match');

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      const matches = cy.nodes().filter((node) => {
        const label = String(node.data('label') || '').toLowerCase();
        return label.includes(q);
      });

      if (matches.length > 0) {
        matches.addClass('search-match');
        cy.animate({
          fit: {
            eles: matches,
            padding: 80,
          },
          duration: 400,
        });
      }
    }
  }, [searchTerm]);

  // Viewport Control Handlers
  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.3);
    }
  };

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 0.7);
    }
  };

  const handleFit = () => {
    if (cyRef.current) {
      cyRef.current.fit(undefined, 40);
    }
  };

  const handleCenterTarget = () => {
    if (!cyRef.current) return;
    const targetNode = cyRef.current.nodes('[?is_target]');
    if (targetNode.length > 0) {
      cyRef.current.animate({
        center: { eles: targetNode },
        zoom: 1.2,
        duration: 400,
      });
    }
  };

  const handleRelayout = () => {
    if (cyRef.current) {
      const layout = cyRef.current.layout(getLayoutConfig(currentLayout));
      layout.run();
    }
  };

  return (
    <div className="relative w-full h-[520px] bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-700/80 rounded-xl overflow-hidden shadow-inner">
      {/* Cytoscape Canvas Target */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Floating Viewport Controls Toolbar */}
      <div className="absolute top-3 right-3 flex items-center gap-1.5 p-1 rounded-lg bg-white/90 dark:bg-navy-900/90 backdrop-blur-sm border border-slate-200/80 dark:border-navy-700 shadow-md z-20">
        <button
          onClick={handleZoomIn}
          className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-navy-800 text-slate-600 dark:text-slate-300 transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-navy-800 text-slate-600 dark:text-slate-300 transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <div className="h-4 w-[1px] bg-slate-200 dark:bg-navy-700 mx-0.5" />
        <button
          onClick={handleFit}
          className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-navy-800 text-slate-600 dark:text-slate-300 transition-colors"
          title="Fit Graph to Viewport"
        >
          <Maximize2 className="h-4 w-4" />
        </button>
        <button
          onClick={handleCenterTarget}
          className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-navy-800 text-brand-500 transition-colors"
          title="Center on Focal Claim"
        >
          <Target className="h-4 w-4" />
        </button>
        <button
          onClick={handleRelayout}
          className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-navy-800 text-slate-600 dark:text-slate-300 transition-colors"
          title="Recalculate Physics Layout"
        >
          <RotateCw className="h-4 w-4" />
        </button>
      </div>

      {/* Floating Layout Selector */}
      <div className="absolute bottom-3 left-3 flex items-center gap-2 p-1.5 rounded-lg bg-white/90 dark:bg-navy-900/90 backdrop-blur-sm border border-slate-200/80 dark:border-navy-700 shadow-md text-xs text-slate-600 dark:text-slate-300 z-20">
        <Sliders className="h-3.5 w-3.5 text-brand-500 ml-1" />
        <span className="text-[11px] font-semibold">Layout:</span>
        <select
          value={currentLayout}
          onChange={(e) => setCurrentLayout(e.target.value as LayoutName)}
          className="bg-transparent text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer pr-1"
        >
          <option value="cose" className="bg-white dark:bg-navy-900">
            Force-Directed (Cose)
          </option>
          <option value="concentric" className="bg-white dark:bg-navy-900">
            Concentric Rings
          </option>
          <option value="circle" className="bg-white dark:bg-navy-900">
            Circular
          </option>
          <option value="breadthfirst" className="bg-white dark:bg-navy-900">
            Hierarchical
          </option>
        </select>
      </div>

      {/* Node/Edge Counter Indicator */}
      <div className="absolute bottom-3 right-3 flex items-center gap-2 px-2.5 py-1 rounded-lg bg-white/90 dark:bg-navy-900/90 backdrop-blur-sm border border-slate-200/80 dark:border-navy-700 shadow-md text-[11px] font-mono text-slate-500 dark:text-slate-400 z-20">
        <span>{nodeCount} Nodes</span>
        <span>•</span>
        <span>{edgeCount} Edges</span>
      </div>
    </div>
  );
};
