"""
Results view for the EyeTracker application
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem
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
        
        # Title
        title_label = QLabel("Test Results")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Results summary section
        summary_group = QGroupBox("Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_label = QLabel("No results available")
        self.summary_label.setStyleSheet("font-size: 16px; margin: 10px;")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        summary_layout.addWidget(self.summary_label)
        
        main_layout.addWidget(summary_group)
        
        # Detailed results section
        details_group = QGroupBox("Detailed Results")
        details_layout = QVBoxLayout(details_group)
        
        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        details_layout.addWidget(self.results_table)
        
        main_layout.addWidget(details_group)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        
        self.print_btn = QPushButton("Print Results")
        self.print_btn.clicked.connect(self.print_results)
        buttons_layout.addWidget(self.print_btn)
        
        self.save_btn = QPushButton("Save Results")
        self.save_btn.clicked.connect(self.save_results)
        buttons_layout.addWidget(self.save_btn)
        
        self.new_test_btn = QPushButton("New Test")
        self.new_test_btn.clicked.connect(self.start_new_test)
        buttons_layout.addWidget(self.new_test_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def set_results(self, results):
        """Set the results to display"""
        self.results = results
        
        if not results:
            self.summary_label.setText("No results available")
            return
        
        # Update summary label
        total_points = results.get('points_shown', 0)
        points_clicked = results.get('points_clicked', 0)
        points_missed = results.get('points_missed', 0)
        false_positives = results.get('false_positives', 0)
        
        # Calculate accuracy percentage
        accuracy = 0
        if total_points > 0:
            accuracy = (points_clicked / total_points) * 100
        
        summary_text = f"Test completed with {accuracy:.1f}% accuracy.\n"
        summary_text += f"Detected {points_clicked} out of {total_points} light points."
        self.summary_label.setText(summary_text)
        
        # Update details table
        self.results_table.setRowCount(0)  # Clear existing rows
        
        # Add rows to table
        metrics = [
            ("Total points shown", total_points),
            ("Points detected", points_clicked),
            ("Points missed", points_missed),
            ("False button presses", false_positives),
            ("Detection accuracy", f"{accuracy:.1f}%"),
        ]
        
        for row, (metric, value) in enumerate(metrics):
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(metric))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(value)))
    
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
                    points_clicked = self.results.get('points_clicked', 0)
                    points_missed = self.results.get('points_missed', 0)
                    false_positives = self.results.get('false_positives', 0)
                    
                    # Calculate accuracy
                    accuracy = 0
                    if total_points > 0:
                        accuracy = (points_clicked / total_points) * 100
                    
                    # Write rows
                    file.write(f"Total points shown,{total_points}\n")
                    file.write(f"Points detected,{points_clicked}\n")
                    file.write(f"Points missed,{points_missed}\n")
                    file.write(f"False button presses,{false_positives}\n")
                    file.write(f"Detection accuracy,{accuracy:.1f}%\n")
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", f"Results saved to {file_path}")
            
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Error saving results: {str(e)}")
    
    def start_new_test(self):
        """Start a new test"""
        if self.parent:
            self.parent.show_calibration_view()