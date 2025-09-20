# graph_manager.py
from collections import defaultdict
from typing import Dict, List, Any
import asyncio
import datetime

# Global graph variable - using adjacency list
graph: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

def calculate_edge_weight(timestamp: datetime.datetime) -> float:
    """
    Calculate weight based on timestamp distance from now
    
    Args:
        timestamp: The timestamp of the trade
        
    Returns:
        Weight value: 10000 - h^2, where h is hours ago. 0 if h > 100
    """
    now = datetime.datetime.utcnow()
    delta = now - timestamp
    hours_ago = delta.total_seconds() / 3600
    
    if hours_ago > 100:
        return 0.0
    
    weight = 10000 - (hours_ago ** 2)
    return max(0.0, weight)

def add_trade_to_graph(item_a: str, quantity_a: int, item_b: str, quantity_b: int, timestamp: datetime.datetime = None):
    """
    Add a trade to the graph with two directional edges including timestamp
    
    Args:
        item_a: First item name
        quantity_a: Quantity of first item
        item_b: Second item name  
        quantity_b: Quantity of second item
        timestamp: Trade timestamp (defaults to current time if None)
    """
    if timestamp is None:
        timestamp = datetime.datetime.utcnow()
    
    # Calculate exchange rates
    rate_a_to_b = quantity_b / quantity_a if quantity_a > 0 else 0
    rate_b_to_a = quantity_a / quantity_b if quantity_b > 0 else 0
    
    # Calculate current weight for this trade
    current_weight = calculate_edge_weight(timestamp)
    
    # Edge from item_a to item_b
    edge_a_to_b = {
        'trade_to': item_b,
        'rate': rate_a_to_b,
        'quantity_from': quantity_a,
        'quantity_to': quantity_b,
        'timestamp': timestamp,
        'weight': current_weight
    }
    
    # Edge from item_b to item_a
    edge_b_to_a = {
        'trade_to': item_a,
        'rate': rate_b_to_a,
        'quantity_from': quantity_b,
        'quantity_to': quantity_a,
        'timestamp': timestamp,
        'weight': current_weight
    }
    
    # Add edges to graph
    graph[item_a].append(edge_a_to_b)
    graph[item_b].append(edge_b_to_a)
    
    print(f"✅ Added trade edge: {item_a} -> {item_b} (rate: {rate_a_to_b}, weight: {current_weight:.2f})")
    print(f"✅ Added trade edge: {item_b} -> {item_a} (rate: {rate_b_to_a}, weight: {current_weight:.2f})")

async def load_trades_from_db(database):
    """
    Load all trade history from MongoDB and build the graph with timestamps
    
    Args:
        database: MongoDB database instance
    """
    try:
        trade_history_collection = database["Trade-History"]
        
        # Clear existing graph
        graph.clear()
        
        # Load all trades from database
        cursor = trade_history_collection.find({})
        trade_count = 0
        
        async for trade in cursor:
            if all(key in trade for key in ['item_a', 'quantity_a', 'item_b', 'quantity_b']):
                # Get timestamp from trade data, fallback to current time
                timestamp = trade.get('timestamp', datetime.datetime.utcnow())
                
                add_trade_to_graph(
                    trade['item_a'],
                    trade['quantity_a'], 
                    trade['item_b'],
                    trade['quantity_b'],
                    timestamp
                )
                trade_count += 1
        
        print(f"✅ Successfully loaded {trade_count} trades into graph")
        print(f"✅ Graph now contains {len(graph)} items")
        
    except Exception as e:
        print(f"❌ Failed to load trades from database: {str(e)}")
        raise

def find_trade_path(start_item: str, target_item: str, max_depth: int = 3):
    """
    Find all trading paths between two items using DFS with weight calculation
    
    Args:
        start_item: Starting item name
        target_item: Target item name to reach
        max_depth: Maximum path depth to search
        
    Returns:
        List of dictionaries containing path, exchange rate, and weight information
        Format: [{'path': [edge1, edge2, ...], 'rate': total_rate, 'weight': avg_weight}, ...]
    """
    if start_item not in graph:
        for item in graph:
            print(item)
        print(start_item, graph)
        return []
    
    if start_item == target_item:
        return [{'path': [], 'rate': 1.0, 'weight': 10000.0}]
    
    all_paths = []
    
    def dfs(current_item, current_path, current_rate, edge_weights, visited, depth):
        """
        Recursive DFS to find all paths with rate and weight calculation
        
        Args:
            current_item: Current item being explored
            current_path: List of edges in current path
            current_rate: Accumulated exchange rate
            edge_weights: List of weights from edges in current path
            visited: Set of visited items to avoid cycles
            depth: Current search depth
        """
        # Check depth limit
        if depth > max_depth:
            return
        
        # Check if we reached the target
        if current_item == target_item:
            # Calculate average weight of the path
            avg_weight = sum(edge_weights) / len(edge_weights) if edge_weights else 10000.0
            
            all_paths.append({
                'path': current_path.copy(),
                'rate': current_rate,
                'weight': avg_weight
            })
            return
        
        # Explore all neighbors of current item
        for edge in graph[current_item]:
            next_item = edge['trade_to']
            
            # Skip if already visited (avoid cycles)
            if next_item in visited:
                continue
            
            # Add current item to visited set
            visited.add(current_item)
            
            # Calculate new rate by multiplying current rate with edge rate
            new_rate = current_rate * edge['rate']
            
            # Recalculate weight based on current timestamp
            current_edge_weight = calculate_edge_weight(edge['timestamp'])
            
            # Add edge to current path and weight to weights list
            current_path.append(edge)
            edge_weights.append(current_edge_weight)
            
            # Recursively explore next item
            dfs(next_item, current_path, new_rate, edge_weights, visited, depth + 1)
            
            # Backtrack: remove from visited set, current path, and weights
            visited.remove(current_item)
            current_path.pop()
            edge_weights.pop()
    
    # Start DFS from the starting item
    dfs(start_item, [], 1.0, [], set(), 0)
    
    # Sort paths by weight first (highest weight = more recent), then by rate
    all_paths.sort(key=lambda x: (x['weight'], x['rate']), reverse=True)
    
    print(all_paths)
    
    return all_paths

def find_trade_path_detailed(start_item: str, target_item: str, max_depth: int = 3):
    """
    Enhanced version of find_trade_path with detailed path information including weights
    
    Args:
        start_item: Starting item name
        target_item: Target item name to reach
        max_depth: Maximum path depth to search
        
    Returns:
        Dictionary containing comprehensive path analysis with weight information
    """
    paths = find_trade_path(start_item, target_item, max_depth)
    
    if not paths:
        return {
            'start_item': start_item,
            'target_item': target_item,
            'paths_found': 0,
            'paths': [],
            'best_rate': 0.0,
            'best_weight': 0.0,
            'max_depth_used': max_depth
        }
    
    # Calculate statistics including weights
    rates = [path['rate'] for path in paths]
    weights = [path['weight'] for path in paths]
    
    best_rate = max(rates)
    worst_rate = min(rates)
    avg_rate = sum(rates) / len(rates)
    
    best_weight = max(weights)
    worst_weight = min(weights)
    avg_weight = sum(weights) / len(weights)
    
    # Add detailed information to each path
    detailed_paths = []
    for i, path_info in enumerate(paths):
        path_edges = path_info['path']
        
        # Create step-by-step trading instructions with weights
        trading_steps = []
        current_item = start_item
        
        for edge in path_edges:
            current_weight = calculate_edge_weight(edge['timestamp'])
            hours_ago = (datetime.datetime.utcnow() - edge['timestamp']).total_seconds() / 3600
            
            step = {
                'from_item': current_item,
                'to_item': edge['trade_to'],
                'exchange_rate': edge['rate'],
                'edge_weight': current_weight,
                'hours_ago': hours_ago,
                'step_description': f"Trade {current_item} for {edge['trade_to']} at rate {edge['rate']:.4f} (weight: {current_weight:.2f})"
            }
            trading_steps.append(step)
            current_item = edge['trade_to']
        
        detailed_path = {
            'path_id': i + 1,
            'path': path_edges,
            'total_rate': path_info['rate'],
            'path_weight': path_info['weight'],
            'path_length': len(path_edges),
            'trading_steps': trading_steps,
            'final_ratio_description': f"1 {start_item} → {path_info['rate']:.6f} {target_item} (weight: {path_info['weight']:.2f})"
        }
        detailed_paths.append(detailed_path)
    
    return {
        'start_item': start_item,
        'target_item': target_item,
        'paths_found': len(paths),
        'paths': detailed_paths,
        'statistics': {
            'best_rate': best_rate,
            'worst_rate': worst_rate,
            'average_rate': avg_rate,
            'best_weight': best_weight,
            'worst_weight': worst_weight,
            'average_weight': avg_weight,
            'rate_variance': max(rates) - min(rates),
            'weight_variance': max(weights) - min(weights)
        },
        'max_depth_used': max_depth
    }

def get_graph_info():
    """
    Get information about the current graph state including weight statistics
    
    Returns:
        Dict containing graph statistics with weight information
    """
    total_edges = sum(len(edges) for edges in graph.values())
    
    # Calculate weight statistics for all edges
    all_weights = []
    for item_edges in graph.values():
        for edge in item_edges:
            current_weight = calculate_edge_weight(edge['timestamp'])
            all_weights.append(current_weight)
    
    weight_stats = {}
    if all_weights:
        weight_stats = {
            'max_weight': max(all_weights),
            'min_weight': min(all_weights),
            'avg_weight': sum(all_weights) / len(all_weights),
            'total_active_edges': sum(1 for w in all_weights if w > 0)
        }
    
    return {
        "total_items": len(graph),
        "total_edges": total_edges,
        "weight_statistics": weight_stats,
        "items": list(graph.keys()),
        "graph_data": dict(graph)
    }

def update_graph_from_trade(trade_data: Dict[str, Any]):
    """
    Update graph when a new trade is received, including timestamp
    This function is called from the FastAPI endpoint
    
    Args:
        trade_data: Dictionary containing trade information with timestamp
    """
    timestamp = trade_data.get('timestamp', datetime.datetime.utcnow())
    
    add_trade_to_graph(
        trade_data['item_a'],
        trade_data['quantity_a'],
        trade_data['item_b'], 
        trade_data['quantity_b'],
        timestamp
    )

# Additional utility functions for weight analysis
def get_recent_trades_info(hours: int = 24):
    """
    Get information about recent trades within specified hours
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        Dictionary with recent trade statistics
    """
    cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    recent_edges = []
    
    for item, edges in graph.items():
        for edge in edges:
            if edge['timestamp'] > cutoff_time:
                recent_edges.append({
                    'from_item': item,
                    'to_item': edge['trade_to'],
                    'rate': edge['rate'],
                    'timestamp': edge['timestamp'],
                    'weight': calculate_edge_weight(edge['timestamp'])
                })
    
    return {
        'hours_window': hours,
        'recent_trades_count': len(recent_edges),
        'recent_trades': recent_edges
    }

def calculate_recommand_rate(paths: List[Dict]) -> float:
    """
    Calculate weighted average of rates using path weights
    
    Args:
        paths: List of path dictionaries containing 'rate' and 'weight' keys
        
    Returns:
        Weighted average of rates based on path weights
        
    Formula:
        weighted_average = Σ(rate_i × weight_i) / Σ(weight_i)
    """
    if not paths:
        return 0.0
    
    total_weighted_sum = 0.0
    total_weight = 0.0
    
    for path in paths:
        rate = path.get('rate', 0.0)
        weight = path.get('weight', 0.0)
        
        total_weighted_sum += rate * weight
        total_weight += weight
    
    # Avoid division by zero
    if total_weight == 0:
        return 0.0
    
    return total_weighted_sum / total_weight