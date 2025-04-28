from dotenv import load_dotenv
import json
import dash
from dash import dcc, html, callback, Input, Output, State
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
import re

from agent import AlbanianTextAgent

load_dotenv()
# Initialize the agent
agent = AlbanianTextAgent()

# Initialize the Dash app
app = dash.Dash(__name__, title="Albanian Text Analyzer")
server = app.server

# Define color scheme
colors = {
    'background': '#F9F9F9',
    'text': '#333333',
    'primary': '#5C6BC0',
    'secondary': '#7986CB',
    'accent': '#3949AB',
    'success': '#4CAF50',
    'warning': '#FFC107',
    'error': '#F44336',
    'neutral': '#9E9E9E'
}

# Define the app layout
app.layout = html.Div(style={'backgroundColor': colors['background'], 'padding': '20px', 'fontFamily': 'Arial'},
                      children=[
                          html.H1(
                              children='Albanian Text Analysis Tool',
                              style={
                                  'textAlign': 'center',
                                  'color': colors['primary'],
                                  'marginBottom': '30px'
                              }
                          ),

                          html.Div([
                              html.Label('Enter Albanian Text:',
                                         style={'fontSize': '18px', 'fontWeight': 'bold', 'color': colors['text']}),
                              dcc.Textarea(
                                  id='text-input',
                                  placeholder='Type or paste Albanian text here...',
                                  style={
                                      'width': '100%',
                                      'height': '150px',
                                      'padding': '10px',
                                      'border': f'1px solid {colors["primary"]}',
                                      'borderRadius': '5px',
                                      'marginTop': '10px',
                                      'marginBottom': '20px'
                                  }
                              ),

                              html.Div([
                                  html.Label('Select Target Tone (Optional):',
                                             style={'fontSize': '16px', 'color': colors['text']}),
                                  dcc.Dropdown(
                                      id='tone-dropdown',
                                      options=[
                                          {'label': 'No specific tone (show options)', 'value': 'none'},
                                          {'label': 'Formal', 'value': 'formal'},
                                          {'label': 'Informal', 'value': 'informal'},
                                          {'label': 'Friendly', 'value': 'friendly'},
                                          {'label': 'Professional', 'value': 'professional'},
                                          {'label': 'Persuasive', 'value': 'persuasive'},
                                          {'label': 'Enthusiastic', 'value': 'enthusiastic'}
                                      ],
                                      value='none',
                                      style={'marginBottom': '20px'}
                                  )
                              ], style={'width': '50%'}),

                              html.Button(
                                  'Analyze Text',
                                  id='analyze-button',
                                  n_clicks=0,
                                  style={
                                      'backgroundColor': colors['primary'],
                                      'color': 'white',
                                      'border': 'none',
                                      'padding': '10px 20px',
                                      'fontSize': '16px',
                                      'borderRadius': '5px',
                                      'cursor': 'pointer',
                                      'marginBottom': '30px'
                                  }
                              ),

                              # Loading spinner
                              dcc.Loading(
                                  id="loading",
                                  type="circle",
                                  children=[
                                      html.Div(id='analysis-output', style={'marginBottom': '30px'})
                                  ]
                              )
                          ], style={'width': '80%', 'margin': 'auto', 'backgroundColor': 'white', 'padding': '30px',
                                    'borderRadius': '10px', 'boxShadow': '0px 2px 5px rgba(0,0,0,0.1)'}),

                          # Results Section
                          html.Div(id='results-container',
                                   style={'width': '80%', 'margin': 'auto', 'marginTop': '20px', 'display': 'none'},
                                   children=[
                                       # Tab layout for different analysis results
                                       dcc.Tabs(id='analysis-tabs', value='grammar-tab', children=[
                                           dcc.Tab(label='Grammar Analysis', value='grammar-tab', children=[
                                               html.Div(id='grammar-results', className='tab-content')
                                           ], style={'padding': '20px'}),

                                           dcc.Tab(label='Tone Analysis', value='tone-tab', children=[
                                               html.Div(id='tone-results', className='tab-content'),
                                               html.Div(id='tone-chart-container',
                                                        style={'height': '400px', 'marginTop': '20px'})
                                           ], style={'padding': '20px'}),

                                           dcc.Tab(label='Tone Alternatives', value='alternatives-tab', children=[
                                               html.Div(id='alternatives-results', className='tab-content')
                                           ], style={'padding': '20px'})
                                       ], style={'marginTop': '20px'})
                                   ]),

                          # Store the analysis results in a hidden div
                          html.Div(id='analysis-results-store', style={'display': 'none'})
                      ])


# Callback to process the text and update results
@app.callback(
    [
        Output('analysis-results-store', 'children'),
        Output('results-container', 'style')
    ],
    [Input('analyze-button', 'n_clicks')],
    [
        State('text-input', 'value'),
        State('tone-dropdown', 'value')
    ]
)
def analyze_text(n_clicks, input_text, target_tone):
    if n_clicks == 0 or not input_text:
        raise PreventUpdate

    # Prepare the target tone (None if "none" is selected)
    if target_tone == 'none':
        target_tone = None

    try:
        # Run the analysis
        result = agent.forward(input_text, target_tone)

        # Store the results for each analysis type
        # Since we're getting plain text from each tool, we need to separate them
        results_dict = {}

        if isinstance(result, dict):
            # If result is already a dictionary, use it directly
            results_dict = result
        else:
            # Try to parse the complete output to separate the different analyses
            # First, try to split by double newlines or section headers
            grammar_analysis = ""
            tone_analysis = ""
            tone_alternatives = ""

            # Check for grammar text section
            if "ORIGINAL TEXT:" in result or "GRAMMATICAL ERRORS:" in result or "CORRECTED TEXT:" in result:
                # Extract everything from the beginning until we find tone indicators
                end_markers = ["TONE:", "FORMALITY LEVEL:", "SENTIMENT:", "ORIGINAL TONE:"]
                end_pos = float('inf')
                for marker in end_markers:
                    pos = result.find(marker)
                    if pos != -1 and pos < end_pos:
                        end_pos = pos

                if end_pos < float('inf'):
                    grammar_analysis = result[:end_pos].strip()
                else:
                    # If no tone sections found, take everything
                    grammar_analysis = result.strip()

            # Check for tone analysis section
            tone_indicators = ["TONE:", "FORMALITY LEVEL:", "SENTIMENT:", "TONE ANALYSIS:"]
            has_tone_indicators = any(indicator in result for indicator in tone_indicators)

            if has_tone_indicators:
                # Find the first tone indicator
                start_pos = float('inf')
                for indicator in tone_indicators:
                    pos = result.find(indicator)
                    if pos != -1 and pos < start_pos:
                        start_pos = pos

                # Find the end of tone section
                end_markers = ["ORIGINAL TONE:", "FORMAL TONE VERSION:", "FRIENDLY TONE VERSION:", "TARGET TONE:"]
                end_pos = float('inf')
                for marker in end_markers:
                    pos = result.find(marker)
                    if pos != -1 and pos < end_pos:
                        end_pos = pos

                if start_pos < float('inf') and end_pos < float('inf'):
                    tone_analysis = result[start_pos:end_pos].strip()
                elif start_pos < float('inf'):
                    # If no alternative indicators, take everything after tone start
                    tone_analysis = result[start_pos:].strip()

            # Check for tone alternatives section
            alt_indicators = ["ORIGINAL TONE:", "FORMAL TONE VERSION:", "FRIENDLY TONE VERSION:", "TARGET TONE:",
                              "REWRITTEN TEXT:"]
            has_alt_indicators = any(indicator in result for indicator in alt_indicators)

            if has_alt_indicators:
                # Find the first alternative indicator
                start_pos = float('inf')
                for indicator in alt_indicators:
                    pos = result.find(indicator)
                    if pos != -1 and pos < start_pos:
                        start_pos = pos

                if start_pos < float('inf'):
                    tone_alternatives = result[start_pos:].strip()

            results_dict = {
                "grammar_analysis": grammar_analysis if grammar_analysis else result,
                "tone_analysis": tone_analysis if tone_analysis else result,
                "tone_alternatives": tone_alternatives if tone_alternatives else result
            }

        # Show the results container
        return json.dumps(results_dict), {'width': '80%', 'margin': 'auto', 'marginTop': '20px', 'display': 'block',
                                          'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px',
                                          'boxShadow': '0px 2px 5px rgba(0,0,0,0.1)'}

    except Exception as e:
        return json.dumps({"error": str(e)}), {'display': 'none'}


# Callback to format and display grammar results
@app.callback(
    Output('grammar-results', 'children'),
    [Input('analysis-results-store', 'children')]
)
def update_grammar_results(results_json):
    if not results_json:
        raise PreventUpdate

    try:
        results = json.loads(results_json)

        # Get grammar analysis text
        grammar_text = results.get('grammar_analysis', '')
        if not grammar_text:
            return html.Div([
                html.H3('Grammar Analysis', style={'color': colors['primary']}),
                html.P("No grammar analysis available", style={'color': colors['neutral']})
            ])

        # Create the grammar elements
        grammar_elements = [
            html.H3('Grammar Analysis Results', style={'color': colors['primary'], 'marginBottom': '20px'}),
        ]

        # Extract sections with improved parsing
        original_text = extract_text_between(grammar_text, "ORIGINAL TEXT:",
                                             ["GRAMMATICAL ERRORS:", "CORRECTED TEXT:"])

        errors_text = extract_text_between(grammar_text, "GRAMMATICAL ERRORS:",
                                           ["CORRECTED TEXT:", "TONE:", "ORIGINAL TONE:"])

        corrected_text = extract_text_between(grammar_text, "CORRECTED TEXT:",
                                              ["TONE:", "FORMALITY LEVEL:", "SENTIMENT:", "ORIGINAL TONE:"])

        # Display original text
        if original_text:
            grammar_elements.append(html.Div([
                html.H4('Original Text:', style={'marginBottom': '10px', 'color': colors['primary']}),
                html.P(original_text, style={'padding': '15px', 'backgroundColor': '#f8f8f8',
                                             'borderRadius': '5px', 'margin': '0 0 20px 0',
                                             'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
            ]))

        # Handle grammatical errors
        if errors_text:
            if "No grammatical errors found" in errors_text:
                grammar_elements.append(html.Div([
                    html.Div([
                        html.Div([
                            html.Span("✓",
                                      style={'fontSize': '24px', 'marginRight': '10px', 'color': colors['success']}),
                            html.Span("No grammar errors found!",
                                      style={'fontSize': '18px', 'color': colors['success'], 'fontWeight': 'bold'})
                        ], style={'display': 'flex', 'alignItems': 'center'})
                    ], style={'padding': '15px', 'backgroundColor': '#e8f5e9', 'borderRadius': '5px',
                              'margin': '0 0 20px 0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
                ]))
            else:
                # Parse the errors
                errors = []
                current_error = {}
                number_pattern = re.compile(r'^\d+\.\s')

                # Try to parse numbered list format
                if re.search(number_pattern, errors_text):
                    error_items = re.split(number_pattern, errors_text)
                    # First item may be empty or header text
                    error_items = [item for item in error_items if item.strip()]

                    for item in error_items:
                        lines = item.split('\n')
                        error_detail = {}

                        for line in lines:
                            line = line.strip()
                            if "Error:" in line:
                                error_detail["error_text"] = line.split("Error:")[1].strip()
                            elif "Correction:" in line:
                                error_detail["correction"] = line.split("Correction:")[1].strip()
                            elif "Explanation:" in line:
                                error_detail["explanation"] = line.split("Explanation:")[1].strip()

                        if "error_text" in error_detail:
                            errors.append(error_detail)

                # If we couldn't parse numbered list, try line-by-line
                if not errors:
                    lines = errors_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if "Error:" in line:
                            if current_error and "error_text" in current_error:
                                errors.append(current_error)
                                current_error = {}
                            current_error["error_text"] = line.split("Error:")[1].strip()
                        elif "Correction:" in line and current_error:
                            current_error["correction"] = line.split("Correction:")[1].strip()
                        elif "Explanation:" in line and current_error:
                            current_error["explanation"] = line.split("Explanation:")[1].strip()

                    if current_error and "error_text" in current_error:
                        errors.append(current_error)

                # Display the errors
                if errors:
                    grammar_elements.append(html.H4(f'Found {len(errors)} grammar issues:',
                                                    style={'color': colors['primary'], 'marginBottom': '15px'}))

                    error_cards = []
                    for error in errors:
                        error_card = html.Div([
                            html.Div([
                                html.Span('Error: ', style={'fontWeight': 'bold', 'marginRight': '5px'}),
                                html.Span(error.get('error_text', ''), style={'color': colors['error']})
                            ], style={'marginBottom': '8px'}),
                            html.Div([
                                html.Span('Correction: ', style={'fontWeight': 'bold', 'marginRight': '5px'}),
                                html.Span(error.get('correction', ''), style={'color': colors['success']})
                            ], style={'marginBottom': '8px'}),
                            html.Div([
                                html.Span('Explanation: ', style={'fontWeight': 'bold', 'marginRight': '5px'}),
                                html.Span(error.get('explanation', ''))
                            ]) if 'explanation' in error else None
                        ], style={'marginBottom': '15px', 'padding': '15px', 'backgroundColor': '#f8f8f8',
                                  'borderRadius': '5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})

                        error_cards.append(error_card)

                    grammar_elements.append(html.Div(error_cards, style={'marginBottom': '20px'}))
                else:
                    # Fallback display for unparseable error text
                    grammar_elements.append(html.Div([
                        html.H4('Grammar Issues:', style={'color': colors['primary'], 'marginBottom': '10px'}),
                        html.Div(errors_text, style={'padding': '15px', 'backgroundColor': '#f8f8f8',
                                                     'borderRadius': '5px', 'whiteSpace': 'pre-wrap',
                                                     'marginBottom': '20px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
                    ]))

        # Display corrected text
        if corrected_text:
            grammar_elements.append(html.Div([
                html.H4('Corrected Text:', style={'color': colors['primary'], 'marginBottom': '10px'}),
                html.Div(corrected_text, style={'padding': '15px', 'backgroundColor': '#e8f4fc',
                                                'borderRadius': '5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
            ]))

        return html.Div(grammar_elements)

    except Exception as e:
        return html.Div([
            html.H3('Error Processing Grammar Results', style={'color': colors['error']}),
            html.P(str(e))
        ])


# Callback to format and display tone analysis results
@app.callback(

    Output('tone-chart-container', 'children'),

    [Input('analysis-results-store', 'children')]
)
def update_tone_results(results_json):
    if not results_json:
        raise PreventUpdate

    try:
        results = json.loads(results_json)

        # Get tone analysis text
        tone_text = results.get('tone_analysis', '')
        if not tone_text:
            return html.Div([
                html.H3('Tone Analysis', style={'color': colors['primary']}),
                html.P("No tone analysis available", style={'color': colors['neutral']})
            ]), None

        # Extract tone information with improved parsing
        tone = extract_text_between(tone_text, "TONE:", ["FORMALITY LEVEL:", "SENTIMENT:", "TONE ANALYSIS:"])

        formality_level = extract_text_between(tone_text, "FORMALITY LEVEL:",
                                               ["SENTIMENT:", "TONE ANALYSIS:", "ORIGINAL TONE:"])

        sentiment = extract_text_between(tone_text, "SENTIMENT:", ["TONE ANALYSIS:", "ORIGINAL TONE:"])

        tone_analysis = extract_text_between(tone_text, "TONE ANALYSIS:", ["ORIGINAL TONE:"])

        # Create a beautiful tone card
        tone_elements = [
            html.H3('Tone Analysis Results', style={'color': colors['primary'], 'marginBottom': '20px'}),
        ]

        # Create a more attractive tone card
        tone_card = html.Div([
            html.Div([
                html.Div([
                    html.H4('Primary Tone', style={'textAlign': 'center', 'margin': '0', 'color': colors['primary']}),
                    html.Div(tone if tone else "Unknown",
                             style={'fontSize': '24px', 'textAlign': 'center', 'padding': '15px',
                                    'color': colors['accent'], 'fontWeight': 'bold'})
                ], style={'flex': '1', 'padding': '15px', 'backgroundColor': '#f0f7ff',
                          'borderRadius': '5px', 'margin': '0 5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                          'minWidth': '170px'}),

                html.Div([
                    html.H4('Formality', style={'textAlign': 'center', 'margin': '0', 'color': colors['primary']}),
                    html.Div([
                        html.Span(formality_level.split('/')[0].strip() if formality_level and '/' in formality_level
                                  else (extract_number(formality_level) if formality_level else "3"),
                                  style={'fontSize': '24px', 'fontWeight': 'bold'}),
                        html.Span(" / 5", style={'fontSize': '16px'})
                    ], style={'textAlign': 'center', 'padding': '15px'})
                ], style={'flex': '1', 'padding': '15px', 'backgroundColor': '#f0f7ff',
                          'borderRadius': '5px', 'margin': '0 5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                          'minWidth': '170px'}),

                html.Div([
                    html.H4('Sentiment', style={'textAlign': 'center', 'margin': '0', 'color': colors['primary']}),
                    html.Div(sentiment if sentiment else "Neutral",
                             style={'fontSize': '24px', 'textAlign': 'center', 'padding': '15px',
                                    'color': get_sentiment_color(sentiment, colors),
                                    'fontWeight': 'bold'})
                ], style={'flex': '1', 'padding': '15px', 'backgroundColor': '#f0f7ff',
                          'borderRadius': '5px', 'margin': '0 5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                          'minWidth': '170px'})

            ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-between',
                      'marginBottom': '20px'}),

            # Analysis section
            html.Div([
                html.H4('Analysis', style={'marginBottom': '10px', 'color': colors['primary']}),
                html.P(tone_analysis if tone_analysis else "No detailed analysis available.",
                       style={'padding': '15px', 'backgroundColor': '#f8f8f8', 'borderRadius': '5px',
                              'lineHeight': '1.5', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
            ])
        ])

        tone_elements.append(tone_card)

        try:
            # Extract the formality level for the chart
            formality_number = 3  # Default
            if formality_level:
                # Try to extract just the number
                formality_number = extract_number(formality_level) or 3
                formality_number = max(1, min(5, formality_number))  # Ensure between 1-5

            # Determine sentiment value
            sentiment_value = 3  # Default neutral
            if sentiment:
                sentiment_lower = sentiment.lower()
                if 'positive' in sentiment_lower:
                    sentiment_value = 4
                elif 'negative' in sentiment_lower:
                    sentiment_value = 2

            # Create chart data
            categories = ['Formality', 'Sentiment', 'Complexity', 'Directness', 'Emotion']
            values = [formality_number, sentiment_value,
                      formality_number - 1 if formality_number > 1 else 1,
                      3, 4 if sentiment_value > 3 else 2]

            # Ensure values are between 1-5
            values = [max(1, min(5, v)) for v in values]

        except Exception as e:
            tone_chart = html.Div([
                html.P(f"Could not generate tone chart: {str(e)}", style={'color': colors['warning']})
            ])

        return html.Div(tone_elements)

    except Exception as e:
        return html.Div([
            html.H3('Error Processing Tone Results', style={'color': colors['error']}),
            html.P(str(e))
        ]), None


# Callback to format and display tone alternatives
@app.callback(
    Output('alternatives-results', 'children'),
    [Input('analysis-results-store', 'children')]
)
def update_alternatives_results(results_json):
    if not results_json:
        raise PreventUpdate

    try:
        results = json.loads(results_json)

        # Get tone alternatives text
        alternatives_text = results.get('tone_alternatives', '')
        if not alternatives_text:
            return html.Div([
                html.H3('Tone Alternatives', style={'color': colors['primary']}),
                html.P("No tone alternatives available", style={'color': colors['neutral']})
            ])

        # Extract tone alternatives with improved parsing
        original_tone = extract_text_between(alternatives_text, "ORIGINAL TONE:",
                                             ["TARGET TONE:", "FORMAL TONE VERSION:", "FRIENDLY TONE VERSION:"])

        # Create the alternatives elements
        alternatives_elements = [
            html.H3('Tone Alternatives', style={'color': colors['primary'], 'marginBottom': '20px'}),
        ]

        if original_tone:
            alternatives_elements.append(html.Div([
                html.Div([
                    html.Span('Original Tone: ', style={'fontWeight': 'bold', 'marginRight': '5px'}),
                    html.Span(original_tone, style={'color': colors['secondary'], 'fontSize': '16px'})
                ])
            ], style={'marginBottom': '20px', 'padding': '10px 0'}))

        # Check if it's a specific target tone rewrite or multiple options
        target_tone = extract_text_between(alternatives_text, "TARGET TONE:", ["REWRITTEN TEXT:"])
        rewritten_text = extract_text_between(alternatives_text, "REWRITTEN TEXT:", [])

        formal_tone = extract_text_between(alternatives_text, "FORMAL TONE VERSION:",
                                           ["FRIENDLY TONE VERSION:", "PERSUASIVE TONE VERSION:"])

        friendly_tone = extract_text_between(alternatives_text, "FRIENDLY TONE VERSION:",
                                             ["PERSUASIVE TONE VERSION:"])

        persuasive_tone = extract_text_between(alternatives_text, "PERSUASIVE TONE VERSION:", [])

        # Display either single target tone or multiple options
        if target_tone and rewritten_text:
            # Single target tone version
            alternatives_elements.append(html.Div([
                html.H4(f'Text Rewritten in {target_tone} Tone:',
                        style={'color': colors['primary'], 'marginBottom': '10px'}),
                html.Div(rewritten_text, style={'padding': '20px', 'backgroundColor': '#e8f4fc',
                                                'borderRadius': '5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                                                'lineHeight': '1.5'})
            ]))
        elif any([formal_tone, friendly_tone, persuasive_tone]):
            # Multiple tone options
            options = []

            if formal_tone:
                options.append({
                    'tone': 'Formal',
                    'text': formal_tone,
                    'color': '#e3f2fd',  # Light blue
                    'icon': '🧐'
                })

            if friendly_tone:
                options.append({
                    'tone': 'Friendly',
                    'text': friendly_tone,
                    'color': '#e8f5e9',  # Light green
                    'icon': '😊'
                })

            if persuasive_tone:
                options.append({
                    'tone': 'Persuasive',
                    'text': persuasive_tone,
                    'color': '#fff8e1',  # Light amber
                    'icon': '✨'
                })

            option_cards = []
            for option in options:
                card = html.Div([
                    html.Div([
                        html.Span(option['icon'], style={'fontSize': '24px', 'marginRight': '10px'}),
                        html.H4(f"{option['tone']} Tone", style={'margin': '0', 'color': colors['primary']})
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px'}),
                    html.Div(option['text'], style={'lineHeight': '1.5'})
                ], style={'padding': '20px', 'backgroundColor': option['color'], 'borderRadius': '5px',
                          'boxShadow': '0 1px 3px rgba(0,0,0,0.1)', 'marginBottom': '20px'})

                option_cards.append(card)

            alternatives_elements.append(html.Div(option_cards))
        else:
            # Fallback display if we couldn't parse properly
            alternatives_elements.append(html.Div([
                html.H4('Tone Alternatives:', style={'color': colors['primary'], 'marginBottom': '10px'}),
                html.Div(alternatives_text,
                         style={'padding': '15px', 'backgroundColor': '#f8f8f8', 'borderRadius': '5px',
                                'whiteSpace': 'pre-wrap', 'lineHeight': '1.5',
                                'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
            ]))

        return html.Div(alternatives_elements)

    except Exception as e:
        return html.Div([
            html.H3('Error Processing Tone Alternatives', style={'color': colors['error']}),
            html.P(str(e))
        ])


# Helper functions to parse text output

def extract_text_between(text, start_marker, end_markers):
    """
    Extract text between a start marker and the first occurrence of any end marker.

    Args:
        text: The text to search in
        start_marker: The starting marker
        end_markers: List of possible end markers

    Returns:
        Extracted text or empty string if not found
    """
    if not text or not start_marker:
        return ""

    # Find the start position
    start_pos = text.find(start_marker)
    if start_pos == -1:
        return ""

    # Move past the start marker
    start_pos += len(start_marker)

    # Find the earliest end marker
    end_pos = len(text)
    for marker in end_markers:
        if not marker:
            continue
        pos = text.find(marker, start_pos)
        if pos != -1 and pos < end_pos:
            end_pos = pos

    # Extract the text
    extracted = text[start_pos:end_pos].strip()
    return extracted


def extract_number(text):
    """Extract the first number found in text."""
    if not text:
        return None

    # Find all numbers in the text
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(numbers[0])
    return None


def get_sentiment_color(sentiment, colors):
    """Get appropriate color for sentiment."""
    if not sentiment:
        return colors['neutral']

    sentiment_lower = sentiment.lower()
    if 'positive' in sentiment_lower:
        return colors['success']
    elif 'negative' in sentiment_lower:
        return colors['error']
    else:
        return colors['neutral']


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
