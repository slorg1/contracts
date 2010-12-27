import unittest

from contracts import new_contract, check
from contracts.library.extensions import identifier_expression
from contracts.interface import Contract
from contracts.testing.utils import check_contracts_fail, check_contracts_ok
from contracts.main import contracts, can_be_used_as_a_type

# The different patterns

def ok1(x):
    pass

def ok2(x): #@UnusedVariable
    return True

def fail1(x):
    raise ValueError('message')

def fail2(x): #@UnusedVariable
    return False

def invalid_callable1(x): #@UnusedVariable
    return 'ciao'

# generates a new name:
def cname():
    TestNewContract.counter += 1
    return 'GeneratedContract%d' % TestNewContract.counter 
    

class TestNewContract(unittest.TestCase):
    counter = 0
    def test_inverted_args(self):
        self.assertRaises(ValueError, new_contract, ok1, 'list')
    
    def test_wrong_args(self):
        self.assertRaises(ValueError, new_contract, 'my13', 2)
    
    def test_invalid_callable(self):
        self.assertRaises(ValueError, new_contract, 'new', lambda:None)
        
    def test_parsing_error(self):
        self.assertRaises(ValueError, new_contract, 'new', '>>')

    def test_parsing_error2(self):
        # parsing error (unknown spec)
        self.assertRaises(ValueError, new_contract, 'new', 'unknown')
        
    def test_invalid_names(self):
        # invalid names:
        alphabet = 'A B C D E F G H I J K L M N O P Q R S T U W V X Y Z'
        for x in alphabet.split():
            self.assertRaises(ValueError, new_contract, x, 'list')
            self.assertRaises(ValueError, new_contract, x.lower(), 'list')
        self.assertRaises(ValueError, new_contract, 'list', 'list[N]')
        self.assertRaises(ValueError, new_contract, '2acdca', 'list[N]')
        self.assertRaises(ValueError, new_contract, '_', 'list[N]')
    
    def test_valid_identifiers(self):
        examples = ['aa', 'a_', 'a2', 'a_2', 'list2', 'dict2', 'int2',
                    'float2', 'A2', 'array2', 'unit_length']
        
        def check_valid_identifier(e):
            c = identifier_expression.parseString(e, parseAll=True)
            assert isinstance(c, Contract)
            
        for e in examples:
            yield check_valid_identifier, e
        
        for e in examples:
            yield new_contract, e, '*'
            
    def test_valid(self):
        c = new_contract('my_list', 'list[2]')
        assert isinstance(c, Contract)
        check('tuple(my_list, my_list)', ([1, 2], [1, 2]))
        check_contracts_fail('tuple(my_list, my_list)', ([1, 2], [1, 2, 3]))
    
    def test_separate_context(self):
        new_contract('my_list2', 'list[N]')
        check('tuple(my_list2, my_list2)', ([1, 2], [1, 2]))
        check('tuple(my_list2, my_list2)', ([1, 2], [1, 2, 3]))

    def test_renaming(self):
        self.assertNotEqual(ok1, ok2)
        new_contract('my7', ok1)
        self.assertRaises(ValueError, new_contract, 'my7', ok2)
    
    def test_allow_renaming_if_equal1(self):
        new_contract('my8', ok1)
        new_contract('my8', ok1)

    def test_allow_renaming_if_equal2(self):
        new_contract('my8b', 'list[3]')
        new_contract('my8b', 'list[3]')
        
    def test_callable1(self):
        c = cname()
        new_contract(c, ok2)
        check('list(%s)' % c, [0])
        
    def test_callable2(self):
        c = cname()
        new_contract(c, ok2)
        check('list(%s)' % c, [0])
    
    def test_callable3(self):
        c = cname()
        new_contract(c, fail1)
        check_contracts_fail('list(%s)' % c, [0])
        
    def test_callable4(self):
        c = cname()
        new_contract(c, fail2)
        check_contracts_fail('list(%s)' % c, [0])
        
    def test_invalid_callable2(self):
        c = cname()
        new_contract(c, invalid_callable1)
        self.assertRaises(ValueError, check, 'list(%s)' % c, [0])
            
    def test_other_pass(self):
        class Ex1(Exception):
            pass
        def invalid(x):
            raise Ex1()
        c = cname() 
        new_contract(c, invalid)
        self.assertRaises(Ex1, check, 'list(%s)' % c, [0])        

    def test_callable(self):
        class MyTest_ok(object):
            def __call__(self, x): #@UnusedVariable @ 
                return True
        o = MyTest_ok()
        assert o('value') == True
        new_contract(cname(), o)
    
    def test_callable_old_style(self):
        class MyTest_ok():
            def __call__(self, x): #@UnusedVariable @ 
                return True
        o = MyTest_ok()
        assert o('value') == True
        new_contract(cname(), o)
    
    def test_class_as_contract1(self):
        # This should be interpreted as a type
        # init(x,y) so it is not mistaken for a valid callable
        class NewStyleClass(object):
            def __init__(self, x, y): #@UnusedVariable @ 
                pass
        new_contract(cname(), NewStyleClass)
    
    def test_class_as_contract2(self):
        # old sytle class
        class OldStyleClass():
            def __init__(self, x, y): #@UnusedVariable @ 
                pass
        new_contract(cname(), OldStyleClass)
        
    def test_class_as_contract3(self):
        class NewStyleClass(object):
            def __init__(self, x, y): #@UnusedVariable @ 
                pass
        @contracts(x=NewStyleClass)
        def f(x):
            pass
    
    def test_class_as_contract4(self):
        class OldStyleClass():
            def __init__(self, x, y): #@UnusedVariable @ 
                pass
        @contracts(x=OldStyleClass)
        def f(x):
            pass
    
    def test_callable_5(self):
        class MyTest_ok(object):
            def f(self, x): #@UnusedVariable
                return True
        o = MyTest_ok()
        assert o.f('value') == True
        new_contract(cname(), o.f)
    
    def test_callable_invalid(self):
        class MyTest_fail(object):
            def __call__(self, x, y): #@UnusedVariable
                return True
            
        self.assertRaises(ValueError, new_contract, cname(), MyTest_fail())
        
    def test_lambda_2(self):
        new_contract(cname(), lambda x: True) #@UnusedVariable
        new_contract(cname(), lambda x: None) #@UnusedVariable
    
    def test_lambda_invalid(self):
        f = lambda x, y: True #@UnusedVariable
        self.assertRaises(ValueError, new_contract, cname(), f)
    
    def test_lambda_invalid2(self):
        self.assertRaises(ValueError, new_contract, cname(), lambda: True)

    def test_idioms(self):
        color = new_contract('color', 'list[3](number,>=0,<=1)')
        # Make sure we got it right
        color.check([0, 0, 0])
        color.check([0, 0, 1])
        color.fail([0, 0])
        color.fail([0, 0, 2])
        
        self.assertRaises(ValueError, color.fail, [0, 0, 1])
        
        # Now use ``color`` in other contracts.
        @contracts
        def fill_area(inside, border):
            """ Fill the area inside the current figure.
            
                :type border: color
                :type inside: color
            """
            pass
            
        @contracts
        def fill_gradient(colors):
            """ Use a gradient to fill the area.
            
                :type colors: list(color)
            """
            pass

    def test_as_decorator(self):
        @new_contract
        def even(x):
            return x % 2 == 0
        from contracts import parse
        p = parse('even')
        p.check(2)
        p.check(4)
        p.fail(3)
        p.check(2.0)

    def test_as_decorator_multiple(self):
        @new_contract
        @contracts(x='int')
        def even2(x):
            return x % 2 == 0

        from contracts import parse
        p = parse('even2')
        p.check(2)
        p.fail(3)
        p.fail(2.0) # now fails 

    def test_types_as_contracts(self):
        c = cname()
        new_contract(c, str)
        check_contracts_ok(c, '')
        check_contracts_fail(c, 1)
        
    def test_types_as_contracts2(self):
        c = cname()
        new_contract(c, int)
        check_contracts_ok(c, 1)
        check_contracts_fail(c, '')
        
    def test_well_recognized(self):
        class OldStyleClass():
            def __init__(self, x, y): #@UnusedVariable @ 
                pass
            
        assert can_be_used_as_a_type(OldStyleClass)
        
        class NewStyleClass():
            def __init__(self, x, y): #@UnusedVariable @ 
                pass
        
        assert can_be_used_as_a_type(NewStyleClass)
        
        
