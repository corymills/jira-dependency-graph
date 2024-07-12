import streamlit as st
import requests
import textwrap
from graphviz import Digraph

# Constants
MAX_SUMMARY_LENGTH = 30
JIRA_URL = 'https://businessolver.atlassian.net'

# Logging
def log(*args):
    st.error(' '.join(map(str, args)))

# JiraSearch class
class JiraSearch:
    def __init__(self, url, auth):
        self.__base_url = url
        self.url = url + '/rest/api/latest'
        self.auth = auth
        self.fields = ','.join([
            'key', 'summary', 'status', 'description', 
            'issuetype', 'issuelinks', 'subtasks', 
            'customfield_10008', 'labels', 'parent'
        ]) 

    def get(self, uri, params={}):
        headers = {'Content-Type': 'application/json'}
        url = self.url + uri
        return requests.get(url, params=params, auth=self.auth, headers=headers)

    def query(self, query):
        response = self.get('/search', params={'jql': query, 'fields': self.fields, 'maxResults': 1000})
        response.raise_for_status()
        content = response.json()
        if 'issues' not in content:
            raise ValueError(f"Unexpected response format: {content}")
        return content['issues']

# Function to build graph data
def build_graph_data(jql, jira, link_types, word_wrap):
    def get_key(issue):
        return issue['key']

    def create_node_text(issue_key, fields=None):
        if fields:
            summary = fields.get('summary', 'No Summary')
            status_name = fields['status']['name']
            issuetype = fields['issuetype']['name']

            if word_wrap and len(summary) > MAX_SUMMARY_LENGTH:
                summary = textwrap.fill(summary, MAX_SUMMARY_LENGTH)
            else:
                summary = (summary[:MAX_SUMMARY_LENGTH] + '...') if len(summary) > MAX_SUMMARY_LENGTH + 2 else summary
            summary = summary.replace('"', '\\"')

            label = f"{issuetype} - {issue_key}\\n{summary}"

            border_color = 'gray'
            if status_name == 'Closed':
                border_color = 'green'
            elif status_name == 'Backlog':
                border_color = 'yellow'
        else:
            label = issue_key
            border_color = 'red'

        return label, border_color

    def process_link(issue_key, link):
        direction = 'outward' if 'outwardIssue' in link else 'inward'
        linked_issue = link.get(direction + 'Issue')
        if not linked_issue:
            return None, None

        linked_issue_key = get_key(linked_issue)
        link_type = link['type'].get(direction)

        if not linked_issue_key:
            return None, None

        if link_type not in link_types:
            return None, None

        return linked_issue_key, link_type

    def walk(issue_key):
        if issue_key not in jql_issues:
            return

        issue = jql_issues[issue_key]
        fields = issue['fields']
        seen.add(issue_key)

        node_text, border_color = create_node_text(issue_key, fields)
        nodes[issue_key] = (node_text, border_color)

        if 'subtasks' in fields:
            for subtask in fields['subtasks']:
                subtask_key = get_key(subtask)
                if subtask_key in jql_issues:
                    edges.append((issue_key, subtask_key, ''))
                    if subtask_key not in seen:
                        walk(subtask_key)

        if 'issuelinks' in fields:
            for link in fields['issuelinks']:
                result = process_link(issue_key, link)
                if result:
                    linked_issue_key, link_type = result
                    if linked_issue_key:
                        edges.append((issue_key, linked_issue_key, link_type))
                    if linked_issue_key and linked_issue_key not in seen:
                        walk(linked_issue_key)

    try:
        issues = jira.query(jql)
    except ValueError as e:
        log(f"Error querying JQL: {e}")
        return []

    jql_issues = {issue['key']: issue for issue in issues}
    seen = set()
    nodes = {}
    edges = []

    for issue_key in jql_issues:
        if issue_key not in seen:
            walk(issue_key)

    return nodes, edges

# Function to convert graph to PNG format for download
def convert_graph_to_png(dot):
    return dot.pipe(format='png')

# Streamlit app
st.set_page_config(layout="wide")
st.title('Jira Link Graph')

with st.sidebar:
    user = st.text_input('Jira Username', '')
    password = st.text_input('Jira Password', type='password')
    jql_query = st.text_area('JQL Query')
    word_wrap = st.checkbox('Word Wrap')
    link_types = st.multiselect('Link Types to Show', [
        'is blocked by', 'blocks', 'is cloned by', 'clones', 'created by', 'created', 'is duplicated by', 
        'duplicates', 'opened during git code review in', 'git code review opened', 'split from', 'split to', 
        'is part of Roadmap Epic', 'New Feature Story', 'is child of', 'is parent of', 'added to idea', 
        'is idea for', 'is implemented by', 'implements', 'merged into', 'merged from', 'relates to', 
        'Resolved by', 'Resolves', 'is tested by', 'tests', 'tested by', 'Ticket Bug Introduced', 'is child of parent'
    ], default=['blocks', 'relates to', 'duplicates', 'is child of parent'])

if st.sidebar.button('Generate Graph'):
    if not user or not password:
        st.error("Username and password are required")
    else:
        auth = (user, password)
        jira = JiraSearch(JIRA_URL, auth)

        if jql_query:
            nodes, edges = build_graph_data(
                jql_query, jira, link_types, word_wrap
            )

            if nodes:
                dot = Digraph()

                for node_key, (node_text, border_color) in nodes.items():
                    dot.node(node_key, label=node_text, color=border_color, shape='rect', style='filled', fillcolor='white')

                for edge in edges:
                    dot.edge(edge[0], edge[1], label=edge[2])

                # Convert the graph to PNG format for download
                png_data = convert_graph_to_png(dot)
                st.download_button('Download Graph', png_data, file_name='graph.png', mime='image/png')

                # Render the graph
                st.graphviz_chart(dot)

            else:
                st.error('No data to generate graph')
        else:
            st.error('JQL Query is required')
