"""PDF export functionality for diagnostic reports"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import pandas as pd
from io import BytesIO


def generate_single_match_pdf(match_name, parsed_data, diagnostic_result):
    """Generate PDF report for single match analysis"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    # Title
    story.append(Paragraph("FTC Log Doctor - Diagnostic Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Match info
    story.append(Paragraph(f"Match: {match_name}", styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Health Score Section
    story.append(Paragraph("Robot Health Score", heading_style))
    
    score = diagnostic_result.health_score
    status = "Healthy" if score >= 80 else "Caution" if score >= 60 else "Critical"
    score_color = colors.green if score >= 80 else colors.orange if score >= 60 else colors.red
    
    score_data = [
        ['Health Score', 'Status'],
        [f'{score}/100', status]
    ]
    
    score_table = Table(score_data, colWidths=[2*inch, 2*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, 1), score_color),
        ('TEXTCOLOR', (0, 1), (0, 1), colors.whitesmoke),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (0, 1), 14),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(score_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Key Metrics
    story.append(Paragraph("Key Metrics", heading_style))
    
    avg_loop = parsed_data['loop_time_ms'].mean() if parsed_data['loop_time_ms'].notna().any() else 0
    battery_readings = parsed_data['battery_voltage'].notna().sum()
    disconnect_count = parsed_data['is_disconnect'].sum()
    
    metrics_data = [
        ['Metric', 'Value'],
        ['Total Log Entries', f"{len(parsed_data):,}"],
        ['Battery Readings', f"{battery_readings:,}"],
        ['Avg Loop Time', f"{avg_loop:.1f}ms"],
        ['Disconnect Events', str(disconnect_count)]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Compute Stability
    if diagnostic_result.compute_stability:
        story.append(Paragraph("Computational Stability & Efficiency", heading_style))
        cs = diagnostic_result.compute_stability
        
        compute_data = [
            ['Metric', 'Value'],
            ['Efficiency Score', f"{cs['efficiency_score']}/100"],
            ['Avg Loop Time', f"{cs['mean_loop_time']:.1f}ms"],
            ['Coefficient of Variation', f"{cs['coefficient_variation']:.3f}"],
            ['Jitter Status', 'High' if cs['has_jitter'] else 'Stable'],
            ['Blocking Spikes', f"{cs['blocking_spikes']} ({cs['spike_percentage']:.1f}%)"],
            ['Periodic Latency', 'Yes' if cs['periodic_latency'] else 'No']
        ]
        
        compute_table = Table(compute_data, colWidths=[3*inch, 2*inch])
        compute_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
        ]))
        
        story.append(compute_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Battery Prediction
    if diagnostic_result.battery_prediction:
        story.append(Paragraph("Battery Life Prediction", heading_style))
        pred = diagnostic_result.battery_prediction
        
        battery_data = [
            ['Metric', 'Value'],
            ['Current Voltage', f"{pred['current_voltage']:.2f}V"],
            ['Predicted @ 2:30', f"{pred['predicted_voltage_at_150s']:.2f}V"],
            ['Drain Rate', f"{pred['drain_rate_per_second']*60:.3f}V/min"],
            ['Model Confidence', f"{pred['confidence']*100:.0f}%"],
            ['Match Survival', 'Will Last' if pred['will_survive_match'] else 'May Fail']
        ]
        
        battery_table = Table(battery_data, colWidths=[3*inch, 2*inch])
        battery_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
        ]))
        
        story.append(battery_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Critical Issues
    if len(diagnostic_result.critical_issues) > 0:
        story.append(Paragraph("Critical Issues", heading_style))
        for i, issue in enumerate(diagnostic_result.critical_issues, 1):
            story.append(Paragraph(f"{i}. {issue}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        story.append(Spacer(1, 0.2*inch))
    
    # Warnings
    if len(diagnostic_result.warnings) > 0:
        story.append(Paragraph("Warnings", heading_style))
        for i, warning in enumerate(diagnostic_result.warnings, 1):
            story.append(Paragraph(f"{i}. {warning}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        story.append(Spacer(1, 0.2*inch))
    
    # Recommendations
    story.append(Paragraph("Action Items", heading_style))
    if len(diagnostic_result.recommendations) > 0:
        for i, rec in enumerate(diagnostic_result.recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
    else:
        story.append(Paragraph("No action items - robot is operating normally", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_tournament_pdf(tournament_df, all_match_data):
    """Generate PDF report for tournament analysis"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    # Title
    story.append(Paragraph("FTC Log Doctor - Tournament Analysis", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Tournament info
    story.append(Paragraph(f"Total Matches: {len(tournament_df)}", styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Overall Statistics
    story.append(Paragraph("Overall Statistics", heading_style))
    
    avg_health = tournament_df['health_score'].mean()
    problem_count = len(tournament_df[tournament_df['health_score'] < 50])
    best_match = tournament_df.loc[tournament_df['health_score'].idxmax(), 'match_name']
    
    stats_data = [
        ['Metric', 'Value'],
        ['Total Matches', str(len(tournament_df))],
        ['Average Health Score', f"{avg_health:.1f}/100"],
        ['Problem Matches (< 50)', str(problem_count)],
        ['Best Match', best_match]
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Match Details Table
    story.append(Paragraph("Match-by-Match Summary", heading_style))
    
    # Prepare data
    display_df = tournament_df[['match_number', 'match_name', 'health_score', 'avg_loop_time', 'starting_battery']].copy()
    
    table_data = [['#', 'Match Name', 'Health', 'Loop (ms)', 'Battery (V)']]
    
    for _, row in display_df.iterrows():
        table_data.append([
            str(int(row['match_number'])),
            str(row['match_name'])[:30],
            f"{row['health_score']:.0f}",
            f"{row['avg_loop_time']:.1f}" if pd.notna(row['avg_loop_time']) else 'N/A',
            f"{row['starting_battery']:.2f}" if pd.notna(row['starting_battery']) else 'N/A'
        ])
    
    match_table = Table(table_data, colWidths=[0.4*inch, 2.5*inch, 0.8*inch, 0.9*inch, 1*inch])
    
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
    ]
    
    # Color code health scores
    for i in range(1, len(table_data)):
        try:
            health = float(table_data[i][2])
            if health >= 80:
                table_style.append(('BACKGROUND', (2, i), (2, i), colors.lightgreen))
            elif health >= 60:
                table_style.append(('BACKGROUND', (2, i), (2, i), colors.lightyellow))
            else:
                table_style.append(('BACKGROUND', (2, i), (2, i), colors.lightcoral))
        except:
            pass
    
    match_table.setStyle(TableStyle(table_style))
    story.append(match_table)
    
    # Problem matches detail
    if problem_count > 0:
        story.append(PageBreak())
        story.append(Paragraph("Problem Matches (Health < 50)", heading_style))
        
        problem_matches = tournament_df[tournament_df['health_score'] < 50]
        
        for _, match_row in problem_matches.iterrows():
            match_name = match_row['match_name']
            
            # Find the diagnostic result for this match
            for parsed_data, diagnostic_result, match_metadata in all_match_data:
                if match_metadata['match_name'] == match_name:
                    story.append(Paragraph(f"Match: {match_name} (Health: {diagnostic_result.health_score}/100)", styles['Heading3']))
                    
                    if len(diagnostic_result.critical_issues) > 0:
                        story.append(Paragraph("Critical Issues:", styles['Heading4']))
                        for issue in diagnostic_result.critical_issues:
                            story.append(Paragraph(f"• {issue}", styles['Normal']))
                    
                    if len(diagnostic_result.warnings) > 0:
                        story.append(Paragraph("Warnings:", styles['Heading4']))
                        for warning in diagnostic_result.warnings[:3]:
                            story.append(Paragraph(f"• {warning}", styles['Normal']))
                    
                    story.append(Spacer(1, 0.2*inch))
                    break
    
    doc.build(story)
    buffer.seek(0)
    return buffer
