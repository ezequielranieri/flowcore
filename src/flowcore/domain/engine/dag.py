# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import networkx as nx
from typing import List, Set
from ..dsl.models import WorkflowDefinition

class WorkflowDAG:
    def __init__(self, workflow_def: WorkflowDefinition):
        self.workflow_def = workflow_def
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self):
        """
        Builds a networkx DiGraph from the workflow definition.
        """
        for step in self.workflow_def.steps:
            self.graph.add_node(step.name)
            for next_step_name in step.next_steps:
                self.graph.add_edge(step.name, next_step_name)

    def validate(self) -> bool:
        """
        Verifies that the graph is a Directed Acyclic Graph (no cycles).
        """
        return nx.is_directed_acyclic_graph(self.graph)

    def get_terminal_nodes(self) -> List[str]:
        """
        Returns nodes with no outgoing edges.
        """
        return [node for node, out_degree in self.graph.out_degree() if out_degree == 0]

    def is_workflow_complete(self, completed_step_names: Set[str]) -> bool:
        """
        Determines if the workflow is complete based on real traversal.
        A workflow is complete if all terminal nodes that are REACHABLE from 
        the starting steps (given the logic) have been completed.
        
        Refinement for MVP: For now, if all terminal nodes of the static DAG 
        are in completed_step_names, we consider it complete.
        """
        terminal_nodes = self.get_terminal_nodes()
        if not terminal_nodes:
            return True
            
        return all(node in completed_step_names for node in terminal_nodes)
