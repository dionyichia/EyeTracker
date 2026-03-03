"""
Results view for the EyeTracker application
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog


class ResultsView(QWidget):
    """View for displaying test results"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.results = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 14, 20, 20)
        main_layout.setSpacing(12)

        self.content = QFrame()
        self.content.setMaximumWidth(760)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)

        # Title
        title_label = QLabel("Test Results")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(title_label)

        title_underline = QFrame()
        title_underline.setFrameShape(QFrame.Shape.HLine)
        title_underline.setFixedHeight(1)
        title_underline.setStyleSheet("background-color: #111111;")
        main_layout.addWidget(title_underline)

        self.summary_label = QLabel("No results available")
        self.summary_label.setStyleSheet("font-size: 17px; color: #111111;")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        self.content_layout.addWidget(self.summary_label)

        # Results table (clean, no card title)
        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setShowGrid(True)
        self.results_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_table.setStyleSheet(
            "QTableWidget { border: 2px solid #111111; gridline-color: #111111; border-radius: 10px; background-color: #ffffff; }"
            "QHeaderView::section { border: 1px solid #111111; padding: 4px 6px; font-weight: normal; background-color: #ffffff; color: #111111; }"
            "QTableWidget::item { color: #111111; border-bottom: 1px solid #111111; border-right: 1px solid #111111; }"
        )
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(0, 380)
        header.resizeSection(1, 140)
        self.results_table.horizontalHeader().setFixedHeight(28)
        self.results_table.setCornerButtonEnabled(False)
        value_header = self.results_table.horizontalHeaderItem(1)
        if value_header:
            value_font = value_header.font()
            value_font.setBold(True)
            value_header.setFont(value_font)
        table_wrap = QHBoxLayout()
        table_wrap.addStretch()
        table_wrap.addWidget(self.results_table)
        table_wrap.addStretch()
        self.content_layout.addLayout(table_wrap)
        
        # Buttons row
        button_style = (
            "QPushButton {"
            "background-color: #ffffff; color: #111111; border: 1px solid #111111;"
            "border-radius: 7px; font-weight: bold; font-size: 13px; padding: 6px 10px;"
            "min-height: 30px; }"
            "QPushButton:hover { background-color: #f5f5f5; }"
        )

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.print_btn = QPushButton("Print Results")
        self.print_btn.setStyleSheet(button_style)
        self.print_btn.setFixedWidth(140)
        self.print_btn.clicked.connect(self.print_results)
        buttons_layout.addWidget(self.print_btn)
        
        self.save_btn = QPushButton("Save Results")
        self.save_btn.setStyleSheet(button_style)
        self.save_btn.setFixedWidth(140)
        self.save_btn.clicked.connect(self.save_results)
        buttons_layout.addWidget(self.save_btn)
        
        self.new_test_btn = QPushButton("New Test")
        self.new_test_btn.setStyleSheet(button_style)
        self.new_test_btn.setFixedWidth(140)
        self.new_test_btn.clicked.connect(self.start_new_test)
        buttons_layout.addWidget(self.new_test_btn)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addLayout(buttons_layout)

        main_layout.addWidget(self.content, 0, Qt.AlignmentFlag.AlignHCenter)
    
    def set_results(self, results):
        """Set the results to display"""
        self.results = results
        
        if not results:
            self.summary_label.setText("No results available")
            return
        
        # Update summary label
        total_points = results.get('points_shown', 0)
        total_clicks = results.get('clicks', 0)
        click_patten = results.get('click_pattern', None)
        if not click_patten:
            points_clicked = 0
            points_missed = 0
        else:
            points_clicked = click_patten.count('1')
            points_missed = click_patten.count('0')
        num_times_look_away = results.get('out_of_thres_counter', 0)


        # True positive - click with theres light
        true_postiive =  points_clicked
        # False positive - click when there is nothing 
        false_positives = total_clicks - points_clicked
        # True negative - no click when there is no light
        # true_postiive =  
        # False negative - no click when there is light
        false_negative = points_missed
        
        # Calculate accuracy percentage
        accuracy = 0
        false_positive_rate = 0
        fixation_loss_rate = 0
        if total_points > 0:
            accuracy = (points_clicked / total_points) * 100
            false_positive_rate = (false_positives / total_points) * 100
            fixation_loss_rate = (num_times_look_away / total_points) * 100
        
        summary_text = (
            f"<span style='font-weight:700'>{points_clicked} / {total_points}</span> points detected at "
            f"<span style='font-weight:700'>{accuracy:.1f}%</span> accuracy."
        )
        self.summary_label.setText(summary_text)

        # Update details table
        self.results_table.setRowCount(0)  # Clear existing rows
        
        # Add rows to table
        metrics = [
            ("Total points shown", total_points),
            ("Points detected", points_clicked),
            ("Points missed", points_missed),
            ("False button presses", false_positives),
            ("Number of times looked away", num_times_look_away),
            ("Detection accuracy", f"{accuracy:.1f}%"),
            ("False positive rate", f"{false_positive_rate:.1f}%"),
            ("Fixation loss rate", f"{fixation_loss_rate:.1f}%"),
        ]
        
        for row, (metric, value) in enumerate(metrics):
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(metric))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(value)))

        # Lock table size to avoid scrollbars (fixed 8 rows)
        self.results_table.resizeRowsToContents()
        header_h = self.results_table.horizontalHeader().height()
        rows_h = sum(self.results_table.rowHeight(r) for r in range(self.results_table.rowCount()))
        frame = self.results_table.frameWidth() * 2
        self.results_table.setFixedHeight(header_h + rows_h + frame)

        total_width = self.results_table.horizontalHeader().length()
        total_width += self.results_table.verticalHeader().width()
        total_width += frame
        self.results_table.setFixedWidth(total_width)

        if hasattr(self, "content") and self.content:
            self.content.setFixedWidth(self.results_table.width())
    
    def print_results(self):
        """Print the test results"""
        if not self.results:
            return
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            # TODO: Implement actual printing logic
            # For now, just show a message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Print", "Printing functionality will be implemented.")
    
    def save_results(self):
        """Save the test results to a file"""
        if not self.results:
            return
        
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    # Write header
                    file.write("Metric,Value\n")
                    
                    # Write data
                    total_points = self.results.get('points_shown', 0)
                    total_clicks = self.results.get('clicks', 0)
                    click_pattern = self.results.get('click_pattern', None)
                    if not click_pattern:
                        points_clicked = 0
                        points_missed = 0
                    else:
                        points_clicked = click_pattern.count('1')
                        points_missed = click_pattern.count('0')

                    num_times_look_away = self.results.get('out_of_thres_counter', 0)
                    false_positives = total_clicks - points_clicked
                    
                    accuracy = 0
                    false_positive_rate = 0
                    fixation_loss_rate = 0
                    if total_points > 0:
                        accuracy = (points_clicked / total_points) * 100
                        false_positive_rate = (false_positives / total_points) * 100
                        fixation_loss_rate = (num_times_look_away / total_points) * 100
                    
                    # Write rows
                    file.write(f"Total points shown,{total_points}\n")
                    file.write(f"Points detected,{points_clicked}\n")
                    file.write(f"Points missed,{points_missed}\n")
                    file.write(f"False button presses,{false_positives}\n")
                    file.write(f"Detection accuracy,{accuracy:.1f}%\n")
                    file.write(f"False positive rate,{false_positive_rate:.1f}%\n")
                    file.write(f"Fixation loss rate,{fixation_loss_rate:.1f}%\n")
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", f"Results saved to {file_path}")
            
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Error saving results: {str(e)}")
    
    def start_new_test(self):
        """Start a new test"""
        if self.parent:
            self.parent.show_calibration_view()
