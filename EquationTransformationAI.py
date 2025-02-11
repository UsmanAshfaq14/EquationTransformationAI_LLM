import json
import csv
from typing import Dict, List, Union
import re
from datetime import datetime
from typing import Dict, List, Tuple
from sympy import symbols, expand, factor, solve, simplify, Eq, parse_expr, latex, Symbol
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

class EquationTransformer:
    def __init__(self):
        self.valid_transformations = {"simplify", "factorize", "expand", "isolate_variable"}
        
    def validate_data(self, data: Dict) -> Dict:
        validation_report = {
            "data_structure": {
                "num_equations": 0,
                "fields": []
            },
            "required_fields": {
                "equation_id": False,
                "original_equation": False,
                "transformation_type": False,
                "target_variable": "N/A"
            },
            "data_types": {
                "equation_id": False,
                "original_equation": False,
                "transformation_type": False,
                "target_variable": "N/A"
            },
            "is_valid": True,
            "errors": []
        }
        
        if "equations" not in data:
            validation_report["is_valid"] = False
            validation_report["errors"].append("Missing 'equations' key in data")
            return validation_report
            
        validation_report["data_structure"]["num_equations"] = len(data["equations"])
        
        for equation in data["equations"]:
            # Store detected fields
            validation_report["data_structure"]["fields"] = list(equation.keys())
            
            # Check required fields
            validation_report["required_fields"]["equation_id"] = "equation_id" in equation
            validation_report["required_fields"]["original_equation"] = "original_equation" in equation
            validation_report["required_fields"]["transformation_type"] = "transformation_type" in equation
            
            if equation.get("transformation_type") == "isolate_variable":
                validation_report["required_fields"]["target_variable"] = "target_variable" in equation
                validation_report["data_types"]["target_variable"] = isinstance(equation.get("target_variable"), str)
            
            # Validate data types
            validation_report["data_types"]["equation_id"] = isinstance(equation.get("equation_id"), (str, int))
            validation_report["data_types"]["original_equation"] = isinstance(equation.get("original_equation"), str)
            validation_report["data_types"]["transformation_type"] = equation.get("transformation_type") in self.valid_transformations
            
            # Update validation status
            if not all(validation_report["required_fields"].values()):
                validation_report["is_valid"] = False
            if not all(value for key, value in validation_report["data_types"].items() if key != "target_variable"):
                validation_report["is_valid"] = False
        
        return validation_report

    def format_latex(self, expr) -> str:
        latex_str = latex(expr)
        # Remove unnecessary multiplication symbols and formatting
        latex_str = latex_str.replace('\\left', '').replace('\\right', '')
        latex_str = latex_str.replace('\\cdot', '')  # Remove dot multiplication symbol
        return latex_str

    def parse_equation_str(self, equation_str: str) -> Tuple[Symbol, Symbol]:
        try:
            # Replace ^ with ** for Python-style exponentiation
            equation_str = equation_str.replace('^', '**')
            
            transformations = (standard_transformations + 
                                (implicit_multiplication_application,))
            if "=" in equation_str:
                left, right = equation_str.split("=")
                return (parse_expr(left.strip(), transformations=transformations), 
                        parse_expr(right.strip(), transformations=transformations))
            return (parse_expr(equation_str.strip(), transformations=transformations), 
                    parse_expr("0", transformations=transformations))
        except Exception as e:
            raise ValueError(f"Error parsing equation: {str(e)}")

    def transform_equation(self, equation: Dict) -> Dict:
        result = {
            "equation_id": equation["equation_id"],
            "original_equation": equation["original_equation"],
            "transformation_type": equation["transformation_type"],
            "steps": [],
            "final_result": "",
            "explanation": ""
        }
        
        try:
            left_expr, right_expr = self.parse_equation_str(equation["original_equation"])
            
            if equation["transformation_type"] == "simplify":
                result.update(self._simplify_equation(left_expr, right_expr))
            elif equation["transformation_type"] == "factorize":
                result.update(self._factorize_equation(left_expr, right_expr))
            elif equation["transformation_type"] == "expand":
                result.update(self._expand_equation(left_expr, right_expr))
            elif equation["transformation_type"] == "isolate_variable":
                result.update(self._isolate_variable(left_expr, right_expr, equation["target_variable"]))
        except Exception as e:
            result["steps"] = [{"step": "Error", "formula": str(e), "explanation": "Failed to process equation"}]
            result["final_result"] = "Error"
            result["explanation"] = f"Failed to perform {equation['transformation_type']} transformation"
            
        return result

    def _simplify_equation(self, left_expr, right_expr) -> Dict:
        expr = left_expr - right_expr
        simplified = simplify(expr)
        
        if isinstance(simplified, (int, float)):
            final_result = f"{simplified} = 0"
        else:
            final_result = f"{simplified} = 0"
        
        steps = [
            {
                "step": "Identify like terms",
                "formula": self.format_latex(Eq(expr, 0)),
                "explanation": "Group terms with same variables"
            },
            {
                "step": "Combine like terms",
                "formula": self.format_latex(Eq(simplified, 0)),
                "explanation": "Add coefficients of like terms"
            }
        ]
        
        return {
            "steps": steps,
            "final_result": final_result,
            "explanation": "Successfully simplified the expression"
        }

    def _factorize_equation(self, left_expr, right_expr) -> Dict:
        expr = left_expr - right_expr
        factored = factor(expr)
        
        steps = [
            {
                "step": "Arrange terms",
                "formula": self.format_latex(Eq(expr, 0)),
                "explanation": "Arrange terms in standard form"
            },
            {
                "step": "Factor the expression",
                "formula": self.format_latex(Eq(factored, 0)),
                "explanation": "Extract common factors and identify patterns"
            }
        ]
        
        return {
            "steps": steps,
            "final_result": self.format_latex(Eq(factored, 0)),
            "explanation": "Successfully factored the expression"
        }

    def _expand_equation(self, left_expr, right_expr) -> Dict:
        expr = left_expr - right_expr
        expanded = expand(expr)
        
        steps = [
            {
                "step": "Apply distributive property",
                "formula": self.format_latex(Eq(expr, 0)),
                "explanation": "Multiply terms in parentheses"
            },
            {
                "step": "Combine like terms",
                "formula": self.format_latex(Eq(expanded, 0)),
                "explanation": "Combine similar terms after expansion"
            }
        ]
        
        return {
            "steps": steps,
            "final_result": self.format_latex(Eq(expanded, 0)),
            "explanation": "Successfully expanded the expression"
        }

    def _isolate_variable(self, left_expr, right_expr, variable: str) -> Dict:
        var = Symbol(variable)
        eq = Eq(left_expr, right_expr)
        try:
            solution = solve(eq, var)
            if not solution:
                raise ValueError("No solution found")
                
            steps = [
                {
                    "step": "Original equation",
                    "formula": self.format_latex(eq),
                    "explanation": "Start with the equation"
                },
                {
                    "step": "Solve for variable",
                    "formula": f"{variable} = {self.format_latex(solution[0])}",
                    "explanation": f"Isolate {variable}"
                }
            ]
            
            return {
                "steps": steps,
                "final_result": f"{variable} = {self.format_latex(solution[0])}",
                "explanation": f"Successfully solved for {variable}"
            }
        except Exception as e:
            raise ValueError(f"Unable to solve for {variable}: {str(e)}")

    def process_json_input(self, json_data: str) -> str:
        try:
            data = json.loads(json_data)
            validation_report = self.validate_data(data)
            return self.generate_report(data, validation_report)
        except json.JSONDecodeError:
            return "Error: Invalid JSON format"

    def generate_report(self, data: Dict, validation_report: Dict) -> str:
        report = "# Data Validation Report\n\n"
        
        # Data Structure Check
        report += "## 1. Data Structure Check:\n"
        report += f"- Number of equations received: {validation_report['data_structure']['num_equations']}\n"
        report += f"- Fields per record: {', '.join(validation_report['data_structure']['fields'])}\n\n"
        
        # Required Fields Check
        report += "## 2. Required Fields Check:\n"
        for field, status in validation_report["required_fields"].items():
            status_text = "✓" if status == True else "✗" if status == False else "N/A"
            report += f"- {field}: {status_text}\n"
        report += "\n"
        
        # Data Type & Value Validation
        report += "## 3. Data Type & Value Validation:\n"
        for field, status in validation_report["data_types"].items():
            status_text = "valid" if status == True else "invalid" if status == False else "N/A"
            report += f"- {field}: {status_text}\n"
        report += "\n"
        
        # Validation Summary
        report += "## Validation Summary:\n"
        if validation_report["is_valid"]:
            report += "Data validation is successful! Proceeding with transformation analysis...\n\n"
        else:
            report += "Data validation failed. Please correct the following errors:\n"
            for error in validation_report["errors"]:
                report += f"- {error}\n"
            return report
            
        # Transformation Process
        if validation_report["is_valid"]:
            report += "# Transformation Process\n\n"
            report += f"Total Equations Evaluated: {validation_report['data_structure']['num_equations']}\n\n"
            
            for equation in data["equations"]:
                result = self.transform_equation(equation)
                report += f"## Equation {result['equation_id']}\n\n"
                report += f"### Input Data:\n"
                report += f"- Original Equation: {result['original_equation']}\n"
                report += f"- Transformation Type: {result['transformation_type']}\n"
                if "target_variable" in equation:
                    report += f"- Target Variable: {equation['target_variable']}\n"
                
                report += "\n### Detailed Calculations:\n"
                for step in result["steps"]:
                    report += f"**{step['step']}**\n"
                    report += f"$${step['formula']}$$\n"
                    report += f"{step['explanation']}\n\n"
                
                report += f"### Final Transformed Equation:\n"
                report += f"$${result['final_result']}$$\n\n"
                report += f"### Explanation:\n{result['explanation']}\n\n"

        # Add feedback section
            report += "# Feedback\n\n"
            report += f"Would you like detailed calculations for any specific equation? Rate this analysis (1-5).\n"
        
        return report

def main():
    # Example usage with all transformation types
    json_input = '''
    {
    "equations": [
        {
        "equation_id": "eq101",
        "original_equation": "2x + 3x = 25",
        "transformation_type": "simplify"
        },
        {
        "equation_id": "eq102",
        "original_equation": "4y - 8 = 2y",
        "transformation_type": "isolate_variable",
        "target_variable": "y"
        },
        {
        "equation_id": "eq103",
        "original_equation": "(z+2)(z-4) = 0",
        "transformation_type": "expand"
        },
        {
        "equation_id": "eq104",
        "original_equation": "10a - 5 = 0",
        "transformation_type": "factorize"
        },
        {
        "equation_id": "eq105",
        "original_equation": "6b + 4b = 50",
        "transformation_type": "simplify"
        },
        {
        "equation_id": "eq106",
        "original_equation": "12c - 18 = 0",
        "transformation_type": "factorize"
        },
        {
        "equation_id": "eq107",
        "original_equation": "(d+3)(d-2) = 0",
        "transformation_type": "expand"
        },
        {
        "equation_id": "eq108",
        "original_equation": "9e - 4 = 5e",
        "transformation_type": "isolate_variable",
        "target_variable": "e"
        }
    ]
    }
    '''
    
    transformer = EquationTransformer()
    report = transformer.process_json_input(json_input)
    print(report)

if __name__ == "__main__":
    main()