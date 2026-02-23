DEFAULT_FLOW_JSON = [
  {
    "flowjson":{
      "version": "7.0",
      "data_api_version": "3.0",
      "routing_model": {
        "WELCOME": [
          "RATING"
        ],
        "RATING": [
          "SPECIFIC_FEEDBACK"
        ],
        "SPECIFIC_FEEDBACK": [
          "COMMENTS"
        ],
        "COMMENTS": [
          "THANK_YOU"
        ],
        "THANK_YOU": []
      },
      "screens": [
        {
          "id": "WELCOME",
          "title": "Customer Feedback",
          "data": {},
          "layout": {
            "type": "SingleColumnLayout",
            "children": [
              {
                "type": "Form",
                "name": "welcome_form",
                "children": [
                  {
                    "type": "TextSubheading",
                    "text": "Thank you for using our service!"
                  },
                  {
                    "type": "TextBody",
                    "text": "We'd love to hear your feedback to help us improve our services."
                  },
                  {
                    "type": "Footer",
                    "label": "Start Feedback",
                    "on-click-action": {
                      "name": "navigate",
                      "next": {
                        "type": "screen",
                        "name": "RATING"
                      },
                      "payload": {}
                    }
                  }
                ]
              }
            ]
          }
        },
        {
          "id": "RATING",
          "title": "Overall Rating",
          "data": {},
          "layout": {
            "type": "SingleColumnLayout",
            "children": [
              {
                "type": "Form",
                "name": "rating_form",
                "children": [
                  {
                    "type": "TextSubheading",
                    "text": "Overall Experience"
                  },
                  {
                    "type": "TextBody",
                    "text": "How would you rate your overall experience with our service?"
                  },
                  {
                    "type": "RadioButtonsGroup",
                    "label": "Your rating",
                    "required": "true",
                    "name": "overall_rating",
                    "data-source": [
                      {
                        "id": "5",
                        "title": "Excellent (5/5)"
                      },
                      {
                        "id": "4",
                        "title": "Good (4/5)"
                      },
                      {
                        "id": "3",
                        "title": "Average (3/5)"
                      },
                      {
                        "id": "2",
                        "title": "Below Average (2/5)"
                      },
                      {
                        "id": "1",
                        "title": "Poor (1/5)"
                      }
                    ]
                  },
                  {
                    "type": "Footer",
                    "label": "Continue",
                    "on-click-action": {
                      "name": "navigate",
                      "next": {
                        "type": "screen",
                        "name": "SPECIFIC_FEEDBACK"
                      },
                      "payload": {
                        "overall_rating": "${form.overall_rating}"
                      }
                    }
                  }
                ]
              }
            ]
          }
        },
        {
          "id": "SPECIFIC_FEEDBACK",
          "title": "Specific Feedback",
          "data": {
            "overall_rating": {
              "type": "string",
              "__example__": "4"
            }
          },
          "layout": {
            "type": "SingleColumnLayout",
            "children": [
              {
                "type": "Form",
                "name": "specific_feedback_form",
                "children": [
                  {
                    "type": "TextSubheading",
                    "text": "Specific Aspects"
                  },
                  {
                    "type": "TextBody",
                    "text": "Please rate these specific aspects of our service:"
                  },
                  {
                    "type": "Dropdown",
                    "label": "Service Quality",
                    "required": "true",
                    "name": "service_quality",
                    "data-source": [
                      {
                        "id": "5",
                        "title": "Excellent"
                      },
                      {
                        "id": "4",
                        "title": "Good"
                      },
                      {
                        "id": "3",
                        "title": "Average"
                      },
                      {
                        "id": "2",
                        "title": "Below Average"
                      },
                      {
                        "id": "1",
                        "title": "Poor"
                      }
                    ]
                  },
                  {
                    "type": "Dropdown",
                    "label": "Product Quality",
                    "required": "true",
                    "name": "product_quality",
                    "data-source": [
                      {
                        "id": "5",
                        "title": "Excellent"
                      },
                      {
                        "id": "4",
                        "title": "Good"
                      },
                      {
                        "id": "3",
                        "title": "Average"
                      },
                      {
                        "id": "2",
                        "title": "Below Average"
                      },
                      {
                        "id": "1",
                        "title": "Poor"
                      }
                    ]
                  },
                  {
                    "type": "Dropdown",
                    "label": "Customer Support",
                    "required": "true",
                    "name": "customer_support",
                    "data-source": [
                      {
                        "id": "5",
                        "title": "Excellent"
                      },
                      {
                        "id": "4",
                        "title": "Good"
                      },
                      {
                        "id": "3",
                        "title": "Average"
                      },
                      {
                        "id": "2",
                        "title": "Below Average"
                      },
                      {
                        "id": "1",
                        "title": "Poor"
                      }
                    ]
                  },
                  {
                    "type": "Footer",
                    "label": "Continue",
                    "on-click-action": {
                      "name": "navigate",
                      "next": {
                        "type": "screen",
                        "name": "COMMENTS"
                      },
                      "payload": {
                        "overall_rating": "${data.overall_rating}",
                        "service_quality": "${form.service_quality}",
                        "product_quality": "${form.product_quality}",
                        "customer_support": "${form.customer_support}"
                      }
                    }
                  }
                ]
              }
            ]
          }
        },
        {
          "id": "COMMENTS",
          "title": "Additional Comments",
          "data": {
            "overall_rating": {
              "type": "string",
              "__example__": "4"
            },
            "service_quality": {
              "type": "string",
              "__example__": "5"
            },
            "product_quality": {
              "type": "string",
              "__example__": "4"
            },
            "customer_support": {
              "type": "string",
              "__example__": "3"
            }
          },
          "layout": {
            "type": "SingleColumnLayout",
            "children": [
              {
                "type": "Form",
                "name": "comments_form",
                "children": [
                  {
                    "type": "TextSubheading",
                    "text": "Additional Comments"
                  },
                  {
                    "type": "TextBody",
                    "text": "Would you like to share any additional comments or suggestions?"
                  },
                  {
                    "type": "TextInput",
                    "label": "Your comments",
                    "name": "comments",
                    "required": "false",
                    "input-type": "text"
                  },
                  {
                    "type": "RadioButtonsGroup",
                    "label": "Would you recommend our service to others?",
                    "required": "true",
                    "name": "would_recommend",
                    "data-source": [
                      {
                        "id": "yes",
                        "title": "Yes"
                      },
                      {
                        "id": "no",
                        "title": "No"
                      },
                      {
                        "id": "maybe",
                        "title": "Maybe"
                      }
                    ]
                  },
                  {
                    "type": "Footer",
                    "label": "Submit Feedback",
                    "on-click-action": {
                      "name": "navigate",
                      "next": {
                        "type": "screen",
                        "name": "THANK_YOU"
                      },
                      "payload": {
                        "overall_rating": "${data.overall_rating}",
                        "service_quality": "${data.service_quality}",
                        "product_quality": "${data.product_quality}",
                        "customer_support": "${data.customer_support}",
                        "comments": "${form.comments}",
                        "would_recommend": "${form.would_recommend}"
                      }
                    }
                  }
                ]
              }
            ]
          }
        },
        {
          "id": "THANK_YOU",
          "title": "Thank You",
          "data": {
            "overall_rating": {
              "type": "string",
              "__example__": "4"
            },
            "service_quality": {
              "type": "string",
              "__example__": "5"
            },
            "product_quality": {
              "type": "string",
              "__example__": "4"
            },
            "customer_support": {
              "type": "string",
              "__example__": "3"
            },
            "comments": {
              "type": "string",
              "__example__": "Good service overall"
            },
            "would_recommend": {
              "type": "string",
              "__example__": "yes"
            }
          },
          "terminal": "true",
          "success": "true",
          "layout": {
            "type": "SingleColumnLayout",
            "children": [
              {
                "type": "Form",
                "name": "thank_you_form",
                "children": [
                  {
                    "type": "TextSubheading",
                    "text": "Thank You for Your Feedback!"
                  },
                  {
                    "type": "TextBody",
                    "text": "We appreciate you taking the time to provide your valuable feedback. Your insights help us improve our services for you and all our customers."
                  },
                  {
                    "type": "Footer",
                    "label": "Done",
                    "on-click-action": {
                      "name": "complete",
                      "payload": {
                        "flow_name": "Feedback_Form",
                        "overall_rating": "${data.overall_rating}",
                        "service_quality": "${data.service_quality}",
                        "product_quality": "${data.product_quality}",
                        "customer_support": "${data.customer_support}",
                        "comments": "${data.comments}",
                        "would_recommend": "${data.would_recommend}"
                      }
                    }
                  }
                ]
              }
            ]
          }
        }
      ]
    },
    "name": "Feedback Form",
    "category": "SURVEY",
  },
  {
      "flowjson": {
          "version": "7.0",
          "data_api_version": "3.0",
          "routing_model": {
              "APPOINTMENT": ["DETAILS"],
              "DETAILS": ["SUMMARY"],
              "SUMMARY": ["TERMS"],
              "TERMS": [],
          },
          "screens": [
              {
                  "id": "APPOINTMENT",
                  "title": "Appointment",
                  "data": {
                      "department": {
                          "type": "array",
                          "items": {
                              "type": "object",
                              "properties": {
                                  "id": {"type": "string"},
                                  "title": {"type": "string"},
                              },
                          },
                          "__example__": [
                              {"id": "shopping", "title": "Shopping & Groceries"},
                              {"id": "clothing", "title": "Clothing & Apparel"},
                              {"id": "home", "title": "Home Goods & Decor"},
                              {"id": "electronics", "title": "Electronics & Appliances"},
                              {"id": "beauty", "title": "Beauty & Personal Care"},
                          ],
                      },
                      "location": {
                          "type": "array",
                          "items": {
                              "type": "object",
                              "properties": {
                                  "id": {"type": "string"},
                                  "title": {"type": "string"},
                              },
                          },
                          "__example__": [
                              {"id": "1", "title": "King’s Cross, London"},
                              {"id": "2", "title": "Oxford Street, London"},
                              {"id": "3", "title": "Covent Garden, London"},
                              {"id": "4", "title": "Piccadilly Circus, London"},
                          ],
                      },
                      "is_location_enabled": {
                          "type": "boolean",
                          "__example__": True,
                      },
                      "date": {
                          "type": "array",
                          "items": {
                              "type": "object",
                              "properties": {
                                  "id": {"type": "string"},
                                  "title": {"type": "string"},
                              },
                          },
                          "__example__": [
                              {"id": "2024-01-01", "title": "Mon Jan 01 2024"},
                              {"id": "2024-01-02", "title": "Tue Jan 02 2024"},
                              {"id": "2024-01-03", "title": "Wed Jan 03 2024"},
                          ],
                      },
                      "is_date_enabled": {
                          "type": "boolean",
                          "__example__": True,
                      },
                      "time": {
                          "type": "array",
                          "items": {
                              "type": "object",
                              "properties": {
                                  "id": {"type": "string"},
                                  "title": {"type": "string"},
                              },
                          },
                          "__example__": [
                              {"id": "10:30", "title": "10:30"},
                              {"id": "11:00", "title": "11:00", "enabled": False},
                              {"id": "11:30", "title": "11:30"},
                              {"id": "12:00", "title": "12:00", "enabled": False},
                              {"id": "12:30", "title": "12:30"},
                          ],
                      },
                      "is_time_enabled": {
                          "type": "boolean",
                          "__example__": True,
                      },
                  },
                  "layout": {
                      "type": "SingleColumnLayout",
                      "children": [
                          {
                              "type": "Form",
                              "name": "appointment_form",
                              "children": [
                                  {
                                      "type": "Dropdown",
                                      "label": "Department",
                                      "name": "department",
                                      "data-source": "${data.department}",
                                      "required": True,
                                      "on-select-action": {
                                          "name": "data_exchange",
                                          "payload": {
                                              "trigger": "department_selected",
                                              "department": "${form.department}",
                                          },
                                      },
                                  },
                                  {
                                      "type": "Dropdown",
                                      "label": "Location",
                                      "name": "location",
                                      "data-source": "${data.location}",
                                      "required": "${data.is_location_enabled}",
                                      "enabled": "${data.is_location_enabled}",
                                      "on-select-action": {
                                          "name": "data_exchange",
                                          "payload": {
                                              "trigger": "location_selected",
                                              "department": "${form.department}",
                                              "location": "${form.location}",
                                          },
                                      },
                                  },
                                  {
                                      "type": "Dropdown",
                                      "label": "Date",
                                      "name": "date",
                                      "data-source": "${data.date}",
                                      "required": "${data.is_date_enabled}",
                                      "enabled": "${data.is_date_enabled}",
                                      "on-select-action": {
                                          "name": "data_exchange",
                                          "payload": {
                                              "trigger": "date_selected",
                                              "department": "${form.department}",
                                              "location": "${form.location}",
                                              "date": "${form.date}",
                                          },
                                      },
                                  },
                                  {
                                      "type": "Dropdown",
                                      "label": "Time",
                                      "name": "time",
                                      "data-source": "${data.time}",
                                      "required": "${data.is_time_enabled}",
                                      "enabled": "${data.is_time_enabled}",
                                  },
                                  {
                                      "type": "Footer",
                                      "label": "Continue",
                                      "on-click-action": {
                                          "name": "navigate",
                                          "next": {"type": "screen", "name": "DETAILS"},
                                          "payload": {
                                              "department": "${form.department}",
                                              "location": "${form.location}",
                                              "date": "${form.date}",
                                              "time": "${form.time}",
                                          },
                                      },
                                  },
                              ],
                          }
                      ],
                  },
              },
              {
                  "id": "DETAILS",
                  "title": "Details",
                  "data": {
                      "department": {"type": "string", "__example__": "beauty"},
                      "location": {"type": "string", "__example__": "1"},
                      "date": {"type": "string", "__example__": "2024-01-01"},
                      "time": {"type": "string", "__example__": "11:30"},
                  },
                  "layout": {
                      "type": "SingleColumnLayout",
                      "children": [
                          {
                              "type": "Form",
                              "name": "details_form",
                              "children": [
                                  {"type": "TextInput", "label": "Name", "name": "name", "required": True},
                                  {"type": "TextInput", "label": "Email", "name": "email", "input-type": "email", "required": True},
                                  {"type": "TextInput", "label": "Phone", "name": "phone", "input-type": "phone", "required": True},
                                  {
                                      "type": "TextArea",
                                      "label": "Further details",
                                      "name": "more_details",
                                      "helper-text": "More details about your visit",
                                      "required": False,
                                  },
                                  {
                                      "type": "Footer",
                                      "label": "Continue",
                                      "on-click-action": {
                                          "name": "data_exchange",
                                          "payload": {
                                              "department": "${data.department}",
                                              "location": "${data.location}",
                                              "date": "${data.date}",
                                              "time": "${data.time}",
                                              "name": "${form.name}",
                                              "email": "${form.email}",
                                              "phone": "${form.phone}",
                                              "more_details": "${form.more_details}",
                                          },
                                      },
                                  },
                              ],
                          }
                      ],
                  },
              },
              {
                  "id": "SUMMARY",
                  "title": "Summary",
                  "terminal": True,
                  "data": {
                      "appointment": {
                          "type": "string",
                          "__example__": "Beauty & Personal Care Department at Kings Cross, London\nMon Jan 01 2024 at 11:30.",
                      },
                      "details": {
                          "type": "string",
                          "__example__": "Name: John Doe\nEmail: john@example.com\nPhone: 123456789\n\nA free skin care consultation, please",
                      },
                      "department": {"type": "string", "__example__": "beauty"},
                      "location": {"type": "string", "__example__": "1"},
                      "date": {"type": "string", "__example__": "2024-01-01"},
                      "time": {"type": "string", "__example__": "11:30"},
                      "name": {"type": "string", "__example__": "John Doe"},
                      "email": {"type": "string", "__example__": "john@example.com"},
                      "phone": {"type": "string", "__example__": "123456789"},
                      "more_details": {"type": "string", "__example__": "A free skin care consultation, please"},
                  },
                  "layout": {
                      "type": "SingleColumnLayout",
                      "children": [
                          {
                              "type": "Form",
                              "name": "confirmation_form",
                              "children": [
                                  {"type": "TextHeading", "text": "Appointment"},
                                  {"type": "TextBody", "text": "${data.appointment}"},
                                  {"type": "TextHeading", "text": "Details"},
                                  {"type": "TextBody", "text": "${data.details}"},
                                  {
                                      "type": "OptIn",
                                      "name": "terms",
                                      "label": "I agree to the terms",
                                      "required": True,
                                      "on-click-action": {
                                          "name": "navigate",
                                          "next": {"type": "screen", "name": "TERMS"},
                                          "payload": {},
                                      },
                                  },
                                  {
                                      "type": "Footer",
                                      "label": "Confirm Appointment",
                                      "on-click-action": {
                                          "name": "data_exchange",
                                          "payload": {
                                              "department": "${data.department}",
                                              "location": "${data.location}",
                                              "date": "${data.date}",
                                              "time": "${data.time}",
                                              "name": "${data.name}",
                                              "email": "${data.email}",
                                              "phone": "${data.phone}",
                                              "more_details": "${data.more_details}",
                                          },
                                      },
                                  },
                              ],
                          }
                      ],
                  },
              },
              {
                  "id": "TERMS",
                  "title": "Terms and Conditions",
                  "layout": {
                      "type": "SingleColumnLayout",
                      "children": [
                          {"type": "TextHeading", "text": "Our Terms"},
                          {
                              "type": "TextBody",
                              "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                                      "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
                                      "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. "
                                      "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
                          },
                      ],
                  },
              },
          ],
      },
      "name": "Appointment Booking",
      "category": "SURVEY",
  },
  
  {
    "flowjson":{
        "version": "7.0",
        "screens": [
          {
            "id": "DETAILS",
            "title": "Get help",
            "data": {},
            "terminal": "true",
            "success": "true",
            "layout": {
              "type": "SingleColumnLayout",
              "children": [
                {
                  "type": "Form",
                  "name": "form",
                  "children": [
                    {
                      "type": "TextInput",
                      "name": "Name",
                      "label": "Name",
                      "input-type": "text",
                      "required": "true",
                    },
                    {
                      "type": "TextInput",
                      "label": "Order number",
                      "name": "Order_number",
                      "input-type": "number",
                      "required": "true",
                    },
                    {
                      "type": "RadioButtonsGroup",
                      "label": "Choose a topic",
                     " name": "Choose_a_topic",
                      "data-source": [
                        {
                          "id": "0_Orders_and_payments",
                          "title": "Orders and payments",
                        },
                        {
                          "id": "1_Maintenance",
                          "title": "Maintenance",
                        },
                        {
                          "id": "2_Delivery",
                          "title": "Delivery",
                        },
                        {
                          "id": "3_Returns",
                          "title": "Returns",
                        },
                        {
                          "id": "4_Other",
                          "title": "Other",
                        },
                      ],
                      "required": "true",
                    },
                    {
                      "type": "TextArea",
                      "label": "Description of issue",
                      "required": "false",
                      "name": "Description_of_issue",
                    },
                    {
                      "type": "Footer",
                      "label": "Done",
                      "on-click-action": {
                        "name": "complete",
                        "payload": {
                          "screen_0_Name_0": "${form.Name}",
                          "screen_0_Order_number_1": "${form.Order_number}",
                          "screen_0_Choose_a_topic_2": "${form.Choose_a_topic}",
                          "screen_0_Description_of_issue_3":
                            "${form.Description_of_issue}",
                        },
                      },
                    },
                  ],
                },
              ],
            },
          },
        ],
      },
      "name":"TestFlow",
      "category":"SHOPPING"
  },
  {
  "flowjson":{
    "version": "7.0",
    "data_api_version": "3.0",
    "routing_model": {
      "screen_xbwgen": [
        "screen_vjcxrh"
      ],
      "screen_vjcxrh": [
        "screen_lqonfn"
      ],
      "screen_lqonfn": []
    },
 
  },
  "name": "Delivery Flow",
  "category": "OTHER"
}

]